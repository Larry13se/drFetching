# config.py - Configuration file for Integrated Medicare Processor

# File paths
from datetime import datetime

CREDENTIALS_FILE = "DATA 27-8-2025 - Batch 2.csv"
OUTPUT_FILE = "medicare_results.csv"
SPECIALTY_FILE = "bad specs.csv"
PECOS_FILE = "pecos_data.json"

# Processing settings
PER_ACCOUNT_DELAY = 3  # Seconds between accounts
RESTART_AFTER_N_ACCOUNTS = 1
MAX_RETRIES_PER_ACCOUNT = 3
COOLDOWN_DURATION_MINUTES = 5

# Date filtering
CLAIMS_MONTHS_BACK = 9  # Only process claims from last 9 months

# DR Evaluation settings
DR_EVAL_ENABLED = True  # Set to False to use old method
MAX_PROVIDERS_PER_ACCOUNT = 20
MAX_SUGGESTIONS_PER_ACCOUNT = 10

# Browser timing settings (in seconds)
TYPING_DELAY = (0.02, 0.05)
CLICK_DELAY = (0.01, 0.03)
PAGE_SETTLE = (0.5, 1.0)
CAPTCHA_WAIT = 3
LOGIN_TIMEOUT = 20
CLAIMS_LOAD_TIMEOUT = 20
DETAIL_TIMEOUT = 10
NAVIGATION_TIMEOUT = 10
ERROR_DETECTION_TIMEOUT = 8

# NPI Registry settings
NPI_MAX_RESULTS = 1  # Only get best match
NPI_RETRY_COUNT = 5
NPI_RETRY_DELAY = 1.0

# PECOS settings
PECOS_RATE_LIMIT_DELAY = 0.5  # Seconds between PECOS API calls

# Error patterns for login detection
ERROR_PATTERNS = {
    "INVALID_CREDENTIALS": [
        "username and/or password you entered is incorrect",
        "invalid username or password", 
        "incorrect username or password",
        "username or password doesn't match",
        "doesn't match our records",
        "login failed"
    ],
    "ACCOUNT_DISABLED": [
        "account has been disabled",
        "account is disabled", 
        "account has been locked",
        "try logging into your account later"
    ],
    "SYSTEM_ERROR": [
        "can't process your request at this time",
        "medicare.gov is currently unavailable",
        "system temporarily unavailable"
    ],
    "RATE_LIMITED": [
        "we can't process your request at this time",
        "too many requests",
        "please try again later",
        "temporarily unavailable"
    ]
}

# Debug settings
DEBUG_MODE = False  # Set to True for verbose logging
SAVE_DEBUG_INFO = True  # Save detailed debug information
GENERATE_PROCESSING_REPORT = True  # Generate detailed processing report

# Selenium settings
BROWSER_OPTIONS = {
    'headless': False,  # Set to True for headless mode
    'user_data_dir': None,  # Browser profile directory
    'disable_extensions': True,
    'disable_plugins': True,
    'disable_images': False,  # Set to True to speed up loading
    'window_size': (1920, 1080)
}

# Company detection patterns (for filtering out organizations)
COMPANY_INDICATORS = [
    " LLC", " INC", " LLP", " LTD", " PLLC", " P.L.L.C", " P.C.", " PC", 
    " CORP", " CORPORATION", " MEDICAL CENTER", " CENTER", " CLINIC", 
    " GROUP", " ASSOCIATES", " ASSOC", " HOSPITAL", " HEALTH", " CARE", 
    " SERVICES", " SERVICE", " URGENT CARE", " IMAGING", " LAB", 
    " LABORATORY", " DIAGNOSTIC", " RADIOLOGY", " PHARMACY", 
    " EQUIPMENT", " SUPPLY", " IPA", " ASC", " SURGICAL", 
    " OUTPATIENT", " INPATIENT"
]

# Output format settings
OUTPUT_COLUMNS = [
    'SESSION_FINGERPRINT', 'SESSION_TIMESTAMP', 'USER_AGENT', 
    'SCREEN_RESOLUTION', 'TIMEZONE', 'SESSION_DURATION', 
    'BROWSER_LANGUAGE', 'DR_COUNT', 'DR_SUGGESTIONS_COUNT'
]

# Add DR columns (DR1 through DR20)
for i in range(1, 21):
    OUTPUT_COLUMNS.extend([
        f'DR{i}', f'DR{i}_ADDRESS', f'DR{i}_DATE', 
        f'DR{i}_NPI', f'DR{i}_ENROLLMENT', f'DR{i}_SPECIALTY', f'DR{i}_SOURCE'
    ])

# Add categorized suggestion columns
OUTPUT_COLUMNS.extend([
    'DR_SUGGESTION_BAD_SPECIALTY',     # Doctors with bad specialties
    'DR_SUGGESTION_NOT_FOUND',         # Doctors not found in NPI Registry
    'DR_SUGGESTION_NOT_ENROLLED',      # Doctors not enrolled in PECOS and not good for CN
    'DR_SUGGESTION_OTHER'              # Other failure reasons
])

# Logging configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = f"medicare_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
CONSOLE_LOG = True

# Performance settings
MAX_CONCURRENT_SESSIONS = 1  # Only 1 for now to avoid rate limiting
BATCH_SIZE = 50  # Process in batches of this size
MEMORY_CLEANUP_INTERVAL = 10  # Clean up memory every N accounts