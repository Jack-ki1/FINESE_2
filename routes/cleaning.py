from flask import Blueprint, render_template, session, jsonify, request, current_app
import pandas as pd
import numpy as np
from scipy import stats

bp = Blueprint('cleaning', __name__)

@bp.route('/')
def cleaning_page():
    return render_template('cleaning.html', active_tab='cleaning')

@bp.route('/api/analyze', methods=['GET'])
def analyze():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, _ = current_app.dataset_store.load(dataset_id)
    
    issues = []
    
    # Check for missing values
    missing = df.isnull().sum()
    for col in df.columns:
        if missing[col] > 0:
            pct = (missing[col] / len(df)) * 100
            severity = 'High' if pct > 20 else 'Medium' if pct > 5 else 'Low'
            issues.append({
                'column': col,
                'issue': f'Missing values ({missing[col]} rows, {pct:.1f}%)',
                'recommendation': f'Fill with mean/median/mode or drop rows',
                'severity': severity,
                'current_state': f'{missing[col]} nulls'
            })
    
    # Check for duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append({
            'column': 'All',
            'issue': f'Duplicate rows ({dup_count} found)',
            'recommendation': 'Remove duplicate rows',
            'severity': 'High' if dup_count > 100 else 'Medium',
            'current_state': f'{dup_count} duplicates'
        })
    
    # Check data types
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(100)
            try:
                pd.to_numeric(sample, errors='raise')
                issues.append({
                    'column': col,
                    'issue': 'Contains numeric characters but stored as text',
                    'recommendation': "Convert to numeric using pd.to_numeric(..., errors='coerce')",
                    'severity': 'Medium',
                    'current_state': 'object dtype'
                })
            except: pass
            
            try:
                pd.to_datetime(sample, errors='raise', format='mixed')
                issues.append({
                    'column': col,
                    'issue': 'Looks like a date but stored as text',
                    'recommendation': 'Convert to datetime using pd.to_datetime()',
                    'severity': 'Medium',
                    'current_state': 'object dtype'
                })
            except: pass
    
    # Check for outliers in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
        if outliers > 0:
            pct = (outliers / len(df)) * 100
            issues.append({
                'column': col,
                'issue': f'Outliers detected ({outliers} values, {pct:.1f}%)',
                'recommendation': 'Clip to bounds or remove outliers',
                'severity': 'Medium' if pct < 10 else 'High',
                'current_state': f'{outliers} outliers'
            })
    
    return jsonify({'issues': issues, 'issue_count': len(issues)})

@bp.route('/api/auto_clean', methods=['POST'])
def auto_clean():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    options = request.json
    operations_applied = 0
    
    # Remove duplicates
    if options.get('remove_duplicates'):
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        if removed > 0:
            operations_applied += 1
    
    # Handle missing values
    if options.get('handle_missing'):
        strategy = options.get('missing_strategy', 'mean')
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        for col in numeric_cols:
            if df[col].isnull().any():
                if strategy == 'mean':
                    df[col].fillna(df[col].mean(), inplace=True)
                elif strategy == 'median':
                    df[col].fillna(df[col].median(), inplace=True)
                elif strategy == 'mode':
                    df[col].fillna(df[col].mode()[0], inplace=True)
                elif strategy == 'zero':
                    df[col].fillna(0, inplace=True)
                elif strategy == 'drop':
                    df = df.dropna(subset=[col])
                operations_applied += 1
        
        for col in categorical_cols:
            if df[col].isnull().any():
                if strategy == 'mode':
                    df[col].fillna(df[col].mode()[0], inplace=True)
                elif strategy == 'drop':
                    df = df.dropna(subset=[col])
                else:
                    df[col].fillna('Unknown', inplace=True)
                operations_applied += 1
    
    # Fix data types
    if options.get('fix_types'):
        for col in df.columns:
            if df[col].dtype == object:
                sample = df[col].dropna().head(100)
                try:
                    pd.to_numeric(sample, errors='raise')
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    operations_applied += 1
                except: pass
                
                try:
                    pd.to_datetime(sample, errors='raise', format='mixed')
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    operations_applied += 1
                except: pass
    
    # Handle outliers
    if options.get('outlier_treatment') != 'none':
        method = options['outlier_treatment']
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            
            if method == 'clip':
                df[col] = df[col].clip(lower, upper)
                operations_applied += 1
            elif method == 'remove':
                mask = (df[col] >= lower) & (df[col] <= upper)
                df = df[mask]
                operations_applied += 1
    
    # Text normalization
    if options.get('text_normalization') != 'none':
        method = options['text_normalization']
        for col in categorical_cols:
            if method == 'lower':
                df[col] = df[col].str.lower()
            elif method == 'upper':
                df[col] = df[col].str.upper()
            elif method == 'strip':
                df[col] = df[col].str.strip()
            operations_applied += 1
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({
        'new_dataset_id': new_id,
        'shape': list(df.shape),
        'operations_applied': operations_applied
    })

@bp.route('/api/apply', methods=['POST'])
def apply_fixes():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    df, name = current_app.dataset_store.load(dataset_id)
    fixes = request.json.get('fixes', [])
    log = []
    for fix in fixes:
        col, action = fix['column'], fix['action']
        if action == 'to_numeric':
            df[col] = pd.to_numeric(df[col], errors='coerce'); log.append(f"Converted {col} to numeric")
        elif action == 'to_datetime':
            df[col] = pd.to_datetime(df[col], errors='coerce'); log.append(f"Converted {col} to datetime")
        elif action == 'drop_na':
            before = len(df); df = df.dropna(subset=[col]); log.append(f"Dropped {before - len(df)} NA rows from {col}")
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    session['cleaning_log'] = session.get('cleaning_log', []) + log
    return jsonify({'new_dataset_id': new_id, 'shape': df.shape, 'log': log,
        'preview': df.head(5).to_dict(orient='records')})

@bp.route('/api/fix_missing', methods=['POST'])
def fix_missing():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    data = request.json
    column = data['column']
    strategy = data['strategy']
    
    if column not in df.columns:
        return jsonify({'error': 'Column not found'}), 400
    
    if strategy == 'drop':
        df = df.dropna(subset=[column])
    elif strategy in ['mean', 'median', 'mode', 'zero']:
        if df[column].dtype in [np.float64, np.int64]:
            if strategy == 'mean':
                df[column].fillna(df[column].mean(), inplace=True)
            elif strategy == 'median':
                df[column].fillna(df[column].median(), inplace=True)
            elif strategy == 'mode':
                df[column].fillna(df[column].mode()[0], inplace=True)
            elif strategy == 'zero':
                df[column].fillna(0, inplace=True)
        else:
            df[column].fillna('Unknown', inplace=True)
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({'success': True, 'shape': list(df.shape)})

@bp.route('/api/remove_duplicates', methods=['POST'])
def remove_duplicates():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({'success': True, 'removed': removed, 'shape': list(df.shape)})

@bp.route('/api/fix_type', methods=['POST'])
def fix_type():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    column = request.json['column']
    
    if column not in df.columns:
        return jsonify({'error': 'Column not found'}), 400
    
    sample = df[column].dropna().head(100)
    try:
        pd.to_numeric(sample, errors='raise')
        df[column] = pd.to_numeric(df[column], errors='coerce')
    except:
        try:
            pd.to_datetime(sample, errors='raise', format='mixed')
            df[column] = pd.to_datetime(df[column], errors='coerce')
        except:
            return jsonify({'error': 'Cannot convert column'}), 400
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({'success': True, 'new_dtype': str(df[column].dtype)})

@bp.route('/api/handle_outliers', methods=['POST'])
def handle_outliers():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    column = request.json['column']
    method = request.json['method']
    
    if column not in df.columns or df[column].dtype not in [np.float64, np.int64]:
        return jsonify({'error': 'Invalid column'}), 400
    
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    
    if method == 'clip':
        df[column] = df[column].clip(lower, upper)
    elif method == 'remove':
        mask = (df[column] >= lower) & (df[column] <= upper)
        df = df[mask]
    elif method == 'cap':
        df[column] = df[column].clip(lower, upper)
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({'success': True, 'shape': list(df.shape)})

@bp.route('/api/quick_fix', methods=['POST'])
def quick_fix():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    column = request.json['column']
    issue = request.json['issue']
    
    # Apply smart fix based on issue type
    if 'missing' in issue.lower() or 'null' in issue.lower():
        if df[column].dtype in [np.float64, np.int64]:
            df[column].fillna(df[column].median(), inplace=True)
        else:
            df[column].fillna('Unknown', inplace=True)
    elif 'duplicate' in issue.lower():
        df = df.drop_duplicates()
    elif 'type' in issue.lower() or 'numeric' in issue.lower():
        df[column] = pd.to_numeric(df[column], errors='coerce')
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({'success': True, 'shape': list(df.shape)})

@bp.route('/api/custom_transform', methods=['POST'])
def custom_transform():
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, name = current_app.dataset_store.load(dataset_id)
    column = request.json['column']
    transform = request.json['transform']
    params = request.json.get('params', '')
    
    if column not in df.columns:
        return jsonify({'error': 'Column not found'}), 400
    
    try:
        if transform == 'log':
            df[column] = np.log1p(df[column].abs())
        elif transform == 'sqrt':
            df[column] = np.sqrt(df[column].abs())
        elif transform == 'square':
            df[column] = df[column] ** 2
        elif transform == 'abs':
            df[column] = df[column].abs()
        elif transform == 'normalize':
            min_val = df[column].min()
            max_val = df[column].max()
            df[column] = (df[column] - min_val) / (max_val - min_val)
        elif transform == 'standardize':
            mean = df[column].mean()
            std = df[column].std()
            df[column] = (df[column] - mean) / std
        elif transform == 'bin':
            bins = int(params.split('=')[1]) if '=' in params else 5
            df[column] = pd.cut(df[column], bins=bins, labels=False)
        elif transform == 'date_extract':
            part = params.split('=')[1] if '=' in params else 'year'
            df[column] = pd.to_datetime(df[column])
            if part == 'year':
                df[column] = df[column].dt.year
            elif part == 'month':
                df[column] = df[column].dt.month
            elif part == 'day':
                df[column] = df[column].dt.day
    except Exception as e:
        return jsonify({'error': f'Transform failed: {str(e)}'}), 400
    
    new_id = current_app.dataset_store.save(df, name)
    session['dataset_id'] = new_id
    current_app.dataset_store.delete(dataset_id)
    
    return jsonify({'success': True, 'shape': list(df.shape)})
