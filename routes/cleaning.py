from flask import Blueprint, render_template, session, jsonify, request, current_app
import pandas as pd
import numpy as np
from scipy import stats
import difflib


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

@bp.route('/api/data-quality', methods=['POST'])
def data_quality():
    """Comprehensive data quality assessment with a 0-100 quality score."""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400

    df, _ = current_app.dataset_store.load(dataset_id)

    if df is None or df.empty:
        return jsonify({'error': 'Dataset is empty'}), 400

    n_rows = len(df)

    # --- Missingness ---
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / n_rows * 100).replace([np.inf, -np.inf], 0)

    missing_heatmap_needed = (missing_counts > 0).sum() > 0
    missingness_summary = {
        'columns_with_missing': int((missing_counts > 0).sum()),
        'max_missing_pct': float(missing_pct.max()) if len(missing_pct) else 0,
        'mean_missing_pct': float(missing_pct.mean()) if len(missing_pct) else 0
    }

    # Suggest imputation strategies per column
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    missing_suggestions = {}
    for col in missing_counts.index[missing_counts > 0].tolist():
        if col in numeric_cols:
            # simple heuristic
            missing_suggestions[col] = {
                'impute_strategy_candidates': ['median', 'mean', 'knn(optional)'],
                'recommended': 'median' if missing_pct[col] < 30 else 'median',
            }
        elif col in categorical_cols:
            missing_suggestions[col] = {
                'impute_strategy_candidates': ['mode', 'new_category(Unknown)'],
                'recommended': 'mode',
            }
        else:
            missing_suggestions[col] = {
                'impute_strategy_candidates': ['unknown'],
                'recommended': 'mode'
            }

    # --- Duplicates & fuzzy matching ---
    exact_dup_rows = int(df.duplicated().sum())

    fuzzy_duplicates = []
    # fuzzy matching only for limited sample to keep it fast
    sample_df = df.head(min(500, len(df))).copy()
    obj_cols_sample = [c for c in sample_df.columns if c in categorical_cols]
    if obj_cols_sample:
        for col in obj_cols_sample[:3]:
            vals = sample_df[col].dropna().astype(str).unique().tolist()
            # compare first N unique values
            vals = vals[:80]
            for i in range(min(30, len(vals))):
                for j in range(i + 1, min(30, len(vals))):
                    a, b = vals[i], vals[j]
                    ratio = difflib.SequenceMatcher(None, a, b).ratio()
                    if ratio >= 0.92 and a != b:
                        fuzzy_duplicates.append({'column': col, 'a': a, 'b': b, 'similarity': ratio})
                        if len(fuzzy_duplicates) >= 10:
                            break
                if len(fuzzy_duplicates) >= 10:
                    break
            if len(fuzzy_duplicates) >= 10:
                break

    # --- Data type validation & auto-correction suggestions ---
    type_issues = []
    type_corrections = []

    for col in df.columns:
        s = df[col]
        if col in numeric_cols:
            # already numeric by dtype; still check if too many non-numeric coercions would be needed
            continue

        if col in categorical_cols:
            # try numeric coercion on sample
            sample = s.dropna().astype(str).head(200)
            if len(sample) >= 10:
                coerced = pd.to_numeric(sample, errors='coerce')
                success_rate = float((~coerced.isna()).sum() / len(sample) * 100)
                # heuristic: if most values look numeric, flag
                if success_rate >= 90:
                    type_issues.append({
                        'column': col,
                        'issue': 'Stored as categorical/text but values look numeric',
                        'success_rate_pct': success_rate,
                    })
                    type_corrections.append({
                        'column': col,
                        'suggested_action': 'Convert to numeric',
                        'method': 'pd.to_numeric(errors="coerce")'
                    })

                # try datetime coercion
                parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
                parsed_rate = float((~parsed.isna()).sum() / len(sample) * 100)
                if parsed_rate >= 80:
                    type_issues.append({
                        'column': col,
                        'issue': 'Stored as categorical/text but values look like dates',
                        'success_rate_pct': parsed_rate,
                    })
                    type_corrections.append({
                        'column': col,
                        'suggested_action': 'Convert to datetime',
                        'method': 'pd.to_datetime(errors="coerce", format="mixed")'
                    })

    # --- Outlier detection (multimethod) ---
    outlier_report = {
        'columns': {},
        'flagged_columns': 0
    }

    # sampling for speed
    outlier_df = df.copy()
    if len(outlier_df) > 5000:
        outlier_df = outlier_df.sample(5000, random_state=42)

    for col in numeric_cols:
        s = outlier_df[col]
        if s.isnull().all():
            continue
        x = s.dropna().values.astype(float)
        if len(x) < 30:
            continue

        z = np.abs(stats.zscore(x, nan_policy='omit')) if len(x) > 1 else np.zeros_like(x)
        z_flags = z > 3

        Q1 = np.nanpercentile(x, 25)
        Q3 = np.nanpercentile(x, 75)
        IQR = Q3 - Q1
        iqr_lower = Q1 - 1.5 * IQR
        iqr_upper = Q3 + 1.5 * IQR
        iqr_flags = (x < iqr_lower) | (x > iqr_upper)

        # IsolationForest / LOF can be heavy; guard with small sampling
        isof_flags = np.zeros_like(x, dtype=bool)
        lof_flags = np.zeros_like(x, dtype=bool)
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.neighbors import LocalOutlierFactor

            iso = IsolationForest(contamination=0.05, random_state=42)
            isof_flags = iso.fit_predict(x.reshape(-1, 1)) == -1

            lof = LocalOutlierFactor(n_neighbors=min(20, max(5, len(x)//20)), contamination=0.05)
            lof_flags = lof.fit_predict(x.reshape(-1, 1)) == -1
        except Exception:
            pass

        # Ensemble vote: flag if >= 3 methods agree
        vote = z_flags.astype(int) + iqr_flags.astype(int) + isof_flags.astype(int) + lof_flags.astype(int)
        ensemble_flags = vote >= 3

        out_pct = float(ensemble_flags.mean() * 100) if len(ensemble_flags) else 0
        if out_pct > 0:
            outlier_report['columns'][col] = {
                'outlier_rate_pct': out_pct,
                'methods': {
                    'zscore>3': float(z_flags.mean() * 100),
                    'iqr_1_5x': float(iqr_flags.mean() * 100),
                    'isolation_forest': float(isof_flags.mean() * 100),
                    'lof': float(lof_flags.mean() * 100)
                }
            }
            outlier_report['flagged_columns'] += 1

    # --- Correlation-based redundancy detection ---
    redundancy = {
        'redundant_pairs': [],
        'redundant_columns': []
    }

    try:
        corr_cols = numeric_cols
        if len(corr_cols) >= 2:
            corr = df[corr_cols].corr(method='pearson').abs()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            threshold = 0.9
            pairs = []
            redundant_cols = set()
            for i, col_a in enumerate(corr.columns):
                for col_b in corr.columns[i+1:]:
                    val = upper.loc[col_a, col_b] if col_b in upper.columns else np.nan
                    if pd.notna(val) and val >= threshold:
                        pairs.append({'a': col_a, 'b': col_b, 'abs_correlation': float(val)})
                        redundant_cols.add(col_a)
                        redundant_cols.add(col_b)
            redundancy['redundant_pairs'] = sorted(pairs, key=lambda x: x['abs_correlation'], reverse=True)[:20]
            redundancy['redundant_columns'] = sorted(list(redundant_cols))
    except Exception:
        pass

    # --- Categorical frequency analysis ---
    categorical_summary = {
        'columns': {}
    }
    for col in categorical_cols[:30]:
        freq = df[col].astype(str).value_counts(dropna=False)
        top = freq.head(10)
        low_freq = freq[freq / max(1, len(df)) < 0.01].head(10)
        categorical_summary['columns'][col] = {
            'top_categories': [{'value': str(k), 'count': int(v)} for k, v in top.items()],
            'low_frequency_warnings': [{'value': str(k), 'share_pct': float((v/len(df))*100)} for k, v in low_freq.items()],
        }

    # --- Quality score (0-100) ---
    # Lower missingness/outliers/duplicates/type issues/redundancy => higher score
    missing_penalty = min(40, missingness_summary['mean_missing_pct'] * 0.8)
    outlier_penalty = min(30, (sum(v['outlier_rate_pct'] for v in outlier_report['columns'].values()) / max(1, len(outlier_report['columns'])) ) if outlier_report['columns'] else 0)
    duplicate_penalty = min(20, (exact_dup_rows / max(1, len(df))) * 100)
    type_penalty = min(15, len(type_corrections) * 5)
    redundancy_penalty = min(15, len(redundancy['redundant_columns']) * 2)

    raw_score = 100 - (missing_penalty + outlier_penalty + duplicate_penalty + type_penalty + redundancy_penalty)
    quality_score = int(max(0, min(100, raw_score)))

    quality_report = {
        'quality_score': quality_score,
        'score_breakdown': {
            'missing_penalty': float(missing_penalty),
            'outlier_penalty': float(outlier_penalty),
            'duplicate_penalty': float(duplicate_penalty),
            'type_penalty': float(type_penalty),
            'redundancy_penalty': float(redundancy_penalty),
        },
        'missingness_summary': missingness_summary,
        'missing_suggestions': missing_suggestions,
        'outliers': outlier_report,
        'type_issues': type_issues[:50],
        'type_corrections': type_corrections[:50],
        'duplicates': {
            'exact_duplicate_rows': exact_dup_rows,
            'fuzzy_duplicate_candidates': fuzzy_duplicates
        },
        'validity': {
            'range_validation': {},
            'categorical_frequencies': categorical_summary
        },
        'redundancy': redundancy
    }

    # Range validation for numeric columns (simple percentile-based bounds)
    range_validation = {}
    for col in numeric_cols:
        s = df[col]
        if s.dropna().shape[0] < 30:
            continue
        lo = float(s.quantile(0.01))
        hi = float(s.quantile(0.99))
        range_validation[col] = {
            'suggested_valid_min': lo,
            'suggested_valid_max': hi,
            'p01': lo,
            'p99': hi
        }
    quality_report['validity']['range_validation'] = range_validation

    return jsonify(quality_report)

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

@bp.route('/api/missingness_matrix', methods=['GET'])
def missingness_matrix():
    """Generate missing data visualization heatmap"""
    dataset_id = session.get('dataset_id')
    if not dataset_id:
        return jsonify({'error': 'No dataset loaded'}), 400
    
    df, _ = current_app.dataset_store.load(dataset_id)
    
    # Create binary matrix (1 = missing, 0 = present)
    missing_binary = df.isnull().astype(int)
    
    import plotly.graph_objects as go
    
    fig = go.Figure(data=go.Heatmap(
        z=missing_binary.values,
        x=missing_binary.columns,
        y=[f'Row {i}' for i in range(len(missing_binary))],
        colorscale=[[0, '#10B981'], [1, '#EF4444']],  # Green to Red
        showscale=True,
        hovertemplate='Column: %{x}<br>Row: %{y}<br>Missing: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Missing Data Matrix (Red = Missing)',
        xaxis_title='Columns',
        yaxis_title='Rows',
        template='plotly_white',
        height=500,
        width=1200
    )
    
    import json
    import plotly.utils
    return jsonify({'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})
