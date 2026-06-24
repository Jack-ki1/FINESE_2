import logging
from flask import Blueprint, jsonify, request
from app.core.data import data_manager
from app.core.cleaning import cleaning_manager
from app.core.ml_models import ml_model_manager

logger = logging.getLogger(__name__)

ai_ops_bp = Blueprint('api_ai_ops', __name__)

# --- Tool registry (deterministic, no external LLM calls) ---

def _tool_suggest_cleaning_operations(dataset_id: str):
    df = data_manager.get_dataset(dataset_id)
    if df is None:
        raise ValueError('Dataset not found')

    issues = cleaning_manager.detect_issues(df)
    recs = cleaning_manager.get_cleaning_recommendations(df)

    # Convert high-level recs to operation suggestions the cleaning pipeline can accept later
    suggested_ops = []

    if issues.get('missing_values'):
        suggested_ops.append({
            'operation': 'fill_missing',
            'strategy': 'median'
        })

    if issues.get('duplicates', 0) > 0:
        suggested_ops.append({
            'operation': 'remove_duplicates'
        })

    if issues.get('outliers'):
        # Keep it simple: outlier removal IQR on numeric columns
        suggested_ops.append({
            'operation': 'remove_outliers',
            'method': 'iqr'
        })

    if issues.get('skewed_columns'):
        suggested_ops.append({
            'operation': 'transform_skewed',
            'method': 'log'
        })

    # Categorical encoding suggestion
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        suggested_ops.append({
            'operation': 'encode_categorical',
            'method': 'label'
        })

    return {
        'issues': issues,
        'recommendations': recs,
        'suggested_operations': suggested_ops
    }


def _tool_recommend_model_type(dataset_id: str, target_col: str):
    df = data_manager.get_dataset(dataset_id)
    if df is None:
        raise ValueError('Dataset not found')

    if target_col not in df.columns:
        raise ValueError('Target column not found')

    # Use the same heuristic as MLModelManager
    X, y = ml_model_manager.prepare_data(df, target_col, feature_columns=None)
    problem_type = ml_model_manager.identify_problem_type(y)

    if problem_type == 'classification':
        candidates = ['random_forest', 'gradient_boosting', 'logistic_regression', 'decision_tree', 'naive_bayes']
    else:
        candidates = ['random_forest', 'gradient_boosting', 'linear_regression', 'ridge', 'lasso']

    return {
        'problem_type': problem_type,
        'recommended_models': candidates
    }


def _tool_generate_report_narrative(dataset_id: str):
    df = data_manager.get_dataset(dataset_id)
    if df is None:
        raise ValueError('Dataset not found')

    desc = df.describe(include='all').to_dict()
    missing = df.isnull().sum().to_dict()

    # Tiny narrative (deterministic template)
    total_missing = sum(v for v in missing.values() if isinstance(v, int))
    narrative = {
        'summary': {
            'rows': int(df.shape[0]),
            'columns': int(df.shape[1]),
            'missing_cells': int(total_missing)
        },
        'high_level_notes': [
            'Review missingness distribution and consider median/mode imputation for skewed columns.',
            'Validate target leakage risks before feature engineering.',
            'Confirm encoding strategy for categorical columns to ensure consistent inference.'
        ],
        'missing_by_column': missing
    }
    return {
        'narrative': narrative,
        'describe_snapshot_keys': list(desc.keys())
    }


TOOL_REGISTRY = {
    'suggest_cleaning_operations': _tool_suggest_cleaning_operations,
    'recommend_model_type': _tool_recommend_model_type,
    'generate_report_narrative': _tool_generate_report_narrative
}


@ai_ops_bp.route('/execute', methods=['POST'])
def execute_tools():
    """
    Tokenized tool execution layer (no authentication).

    Body example:
    {
      "dataset_id": "...",
      "budget_tokens": 120,
      "tools": [
        {"name": "suggest_cleaning_operations", "args": {}},
        {"name": "recommend_model_type", "args": {"target_col": "y"}}
      ]
    }
    """
    body = request.get_json(silent=True) or {}

    dataset_id = body.get('dataset_id')
    tools = body.get('tools') or []
    budget_tokens = int(body.get('budget_tokens', 100))

    if not tools:
        return jsonify({'error': 'tools[] is required'}), 400

    # Budget enforcement: approximate per tool by name length + payload size (deterministic)
    def est_cost(tool_name: str, args: dict):
        args_size = len(str(args or {}))
        return max(1, min(50, len(tool_name) // 2 + args_size // 20))

    remaining = budget_tokens
    trace = []
    outputs = {}

    for step_index, t in enumerate(tools):
        name = t.get('name')
        args = t.get('args') or {}

        if not name or name not in TOOL_REGISTRY:
            return jsonify({'error': f'Unknown tool: {name}'}), 400

        step_cost = est_cost(name, args)
        if remaining - step_cost < 0:
            return jsonify({
                'error': 'Budget exceeded',
                'budget_tokens': budget_tokens,
                'remaining_tokens': remaining,
                'trace': trace
            }), 402

        remaining -= step_cost

        try:
            fn = TOOL_REGISTRY[name]
            # Tool signatures are deterministic:
            # - suggest_cleaning_operations(dataset_id)
            # - generate_report_narrative(dataset_id)
            # - recommend_model_type(dataset_id, target_col=...)
            if name == 'recommend_model_type':
                result = fn(dataset_id, **args)
            else:
                result = fn(dataset_id)

            outputs[name] = result
            trace.append({
                'step': step_index,
                'tool': name,
                'cost': step_cost,
                'status': 'ok'
            })
        except Exception as e:
            trace.append({
                'step': step_index,
                'tool': name,
                'cost': step_cost,
                'status': 'failed',
                'error': str(e)
            })
            return jsonify({
                'error': str(e),
                'trace': trace,
                'outputs_so_far': outputs
            }), 500

    return jsonify({
        'budget_tokens': budget_tokens,
        'remaining_tokens': remaining,
        'outputs': outputs,
        'trace': trace
    }), 200
