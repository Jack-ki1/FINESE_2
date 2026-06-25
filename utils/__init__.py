"""utils package

This module re-exports the public API from the `utils/` submodules.
It intentionally does NOT import the legacy top-level `utils.py` monolith,
so import resolution is deterministic and avoids circular-import hazards.
"""

# Re-export the harmonized utilities
from .data_utils import *  # noqa: F401,F403
from .ml_utils import *  # noqa: F401,F403
from .ui_utils import *  # noqa: F401,F403
from .health_utils import *  # noqa: F401,F403

# Optional dependency availability flags (computed directly)
try:
    from xgboost import XGBClassifier  # noqa: F401
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False

try:
    from lightgbm import LGBMClassifier  # noqa: F401
    LGBM_AVAILABLE = True
except Exception:
    LGBM_AVAILABLE = False

try:
    from catboost import CatBoostClassifier  # noqa: F401
    CATBOOST_AVAILABLE = True
except Exception:
    CATBOOST_AVAILABLE = False

try:
    from imblearn.over_sampling import SMOTE  # noqa: F401
    IMBLEARN_AVAILABLE = True
except Exception:
    IMBLEARN_AVAILABLE = False

try:
    import optuna  # noqa: F401
    OPTUNA_AVAILABLE = True
except Exception:
    OPTUNA_AVAILABLE = False

try:
    import shap  # noqa: F401
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False

__all__ = [
    name for name in globals().keys()
    if not name.startswith('_')
]


