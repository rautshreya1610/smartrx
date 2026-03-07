import os

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = BASE_DIR
DB_PATH     = os.path.join(BASE_DIR, "pharmacy.db")

SECRET_KEY  = "dev-secret-key"
DEBUG       = True
PORT        = 5000

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE     = 100
MAX_AUTOCOMPLETE_RESULTS = 10
DEFAULT_SEARCH_RADIUS_KM = 10.0
MAX_SEARCH_RADIUS_KM     = 100.0
ALERT_WINDOW_DAYS   = 7
CRITICAL_DAYS       = 2
WARNING_DAYS        = 7
LOW_STOCK_THRESHOLD = 10
RATE_LIMIT = 60