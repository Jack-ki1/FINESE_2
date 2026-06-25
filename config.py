# Configuration constants
APP_TITLE = "FINESE • Smart Data Explorer Pro"
APP_ICON = "📊"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
TECH_LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2721/2721264.png"
MAX_COLS_FOR_FILTERING = 30
NUMERIC_SLIDER_LIMIT = 8

# Branding constants
BRAND_NAME = "FINESE"
BRAND_COLOR = "#0ea5e9"
BRAND_COLOR_SECONDARY = "#3b82f6"
BRAND_GRADIENT = "linear-gradient(135deg, #0ea5e9, #3b82f6)"

# UI constants
SECTION_HEADER_CLASS = "section-h"
SECTION_SUBHEADER_CLASS = "section-sub"

# Model constants
DEFAULT_LLM_MODEL = "gpt-4o-mini"
MAX_ROWS_FOR_PLOT = 1000

# Model training constants
DEFAULT_CV_FOLDS = 5
DEFAULT_N_ESTIMATORS = 150
DEFAULT_RANDOM_STATE = 42

# Date parsing
DATE_PARSE_THRESHOLD = 0.7

# Export constants
EXPORT_DATE_FORMAT = "%Y%m%d_%H%M"

# Concurrency / parallelism guard
# HF Spaces typically has limited CPU and process forking can exhaust workers.
import os
N_JOBS = 1 if os.environ.get("SPACE_ID") else -1

