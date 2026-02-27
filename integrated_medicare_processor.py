"""
MEDICARE PROCESSOR - OPTIMIZED VERSION
=======================================
FIXES:
- Single consolidated output file (no more thread-specific files)
- NO MISSING LEADS: Worker threads never exit early, always process all leads
- FASTER: Reduced all delays by 30-50%
- LESS VERBOSE: Minimal logging, only critical messages
- BETTER LOGIN: Multiple retries for password field detection
- ROBUST ERROR HANDLING: Continues processing even after errors
"""

import csv
import os
import random
import time
import json
import hashlib
import threading
from datetime import datetime, date, timedelta, time as dt_time
from seleniumbase import BaseCase
import calendar
import re
import sys
from DR_eval import NPIRegistryService, PECOSEnrollmentService, TaxonomyBasedSpecialtyValidator
from improved_captcha_handler import ImprovedCaptchaHandler

# ===================== CONFIG ===================== #
CREDENTIALS_FILE = "Submission Data - EXPORT (2).csv"
OUTPUT_FILE = "medicare_results_FINAL.csv"  # Single consolidated file
PER_ACCOUNT_DELAY = 1  # Reduced from 3

# SCHEDULED START - Set hours to delay before starting (0 = start immediately)
DELAY_START_HOURS = 0  # Wait 3 hours before starting
DELAY_START_MINUTES = 0  # Additional minutes (optional)

# Threading config
NUM_THREADS = 6
BROWSER_DISTRIBUTION = {
    'chrome': 6
}

# Optimized delays - REDUCED FOR SPEED
TYPING_DELAY = (0.01, 0.02)
CLICK_DELAY = (0.01, 0.02)
PAGE_SETTLE = (0.3, 0.5)
CAPTCHA_WAIT = 2
LOGIN_TIMEOUT = 25
CLAIMS_LOAD_TIMEOUT = 20
DETAIL_TIMEOUT = 10
NAVIGATION_TIMEOUT = 10
ERROR_DETECTION_TIMEOUT = 5

# Retry configuration
MAX_RETRYABLE_ERRORS = 3
RETRYABLE_ERROR_TYPES = [
    "PAGE_LOAD_FAILED",
    "NAVIGATION_FAILED",
    "LOGIN_TIMEOUT",
    "SYSTEM_ERROR",
    "ELEMENT_NOT_FOUND",
    "CAPTCHA_FAILED",  # Added - CAPTCHA failures should be retried
    "PASSWORD_INPUT_FAILED",  # Added - Password input issues should be retried
    "USERNAME_INPUT_FAILED",  # Added - Username input issues should be retried
    "LOGIN_BUTTON_FAILED"  # Added - Login button issues should be retried
]

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

class ThreadSafeCounter:
    """Thread-safe counter for tracking stats"""
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def get(self):
        with self.lock:
            return self.value

success_counter = ThreadSafeCounter()
failure_counter = ThreadSafeCounter()
processed_counter = ThreadSafeCounter()
file_write_lock = threading.Lock()  # Global lock for single output file

class AntiBot:
    """Anti-bot measures and stealth techniques"""

    @staticmethod
    def randomize_delays():
        """Apply random delays to mimic human behavior"""
        return random.uniform(0.5, 2.5)

    @staticmethod
    def random_mouse_movement(driver):
        """Simulate random mouse movements"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            for _ in range(random.randint(2, 5)):
                x = random.randint(0, 1920)
                y = random.randint(0, 1080)
                actions.move_by_offset(x, y).pause(random.uniform(0.1, 0.5))
            actions.perform()
        except:
            pass

    @staticmethod
    def randomize_user_agent_headers(driver):
        """Inject realistic headers"""
        try:
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
        except:
            pass

    @staticmethod
    def inject_stealth_js(driver):
        """Inject stealth scripts to evade detection"""
        try:
            driver.execute_script("""
                const originalQuery = window.chrome.webstore.onInstallStageChanged;
                delete window.chrome;

                Object.defineProperty(window, 'chrome', {
                    get() {
                        return {
                            webstore: {
                                onInstallStageChanged: originalQuery
                            }
                        };
                    }
                });

                const originalQuery2 = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery2(parameters)
                );
            """)
        except:
            pass

class ThreadedMedicareProcessor(BaseCase):

    def __init__(self, *args, browser_type='chrome', thread_id=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.browser_type = browser_type
        self.thread_id = thread_id
        self.cooldown_active = False
        self.processing_lead = False
        
        # Use global single output file
        self.output_file = OUTPUT_FILE
        self.file_lock = file_write_lock  # Use global lock
        
        self.recursion_depth = 0
        self.max_recursion_depth = 5
        self.refresh_count = 0
        self.max_refresh_attempts = 3

        self.npi_service = NPIRegistryService()
        self.pecos_service = PECOSEnrollmentService()
        self.specialty_validator = TaxonomyBasedSpecialtyValidator()
        self.captcha_handler = ImprovedCaptchaHandler(self)
        self.anti_bot = AntiBot()
    def setUp(self):
        super().setUp()
        self.session_start = datetime.now()

        time.sleep(self.anti_bot.randomize_delays())
        self.anti_bot.randomize_user_agent_headers(self.driver)
        self.anti_bot.inject_stealth_js(self.driver)

        # Reduced logging
        pass

    def tearDown(self):
        super().tearDown()
    # 3. Simplified recursion guard - only for truly recursive operations:
    def check_operation_depth(self, operation_name):
        """Check if we're too deep in nested operations"""
        if self.operation_depth >= self.max_operation_depth:
            print(f"[Thread-{self.thread_id}] Max operation depth reached in {operation_name}")
            return False
        return True
    
    def increment_depth(self):
        """Increment operation depth counter"""
        self.operation_depth += 1
    
    def decrement_depth(self):
        """Decrement operation depth counter"""
        self.operation_depth = max(0, self.operation_depth - 1)
    
    def reset_depth(self):
        """Reset operation depth counter"""
        self.operation_depth = 0

    # 4. Simplified safe execution without complex retry logic:
    def safe_page_operation(self, operation_func, operation_name, *args, **kwargs):
        """Safely execute page operations with simple error handling"""
        try:
            result = operation_func(*args, **kwargs)
            return result
        except RecursionError as e:
            print(f"[Thread-{self.thread_id}] RECURSION ERROR in {operation_name} - resetting")
            self.reset_depth()
            return None
        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error in {operation_name}: {str(e)[:150]}")
            return None
    def refresh_page(self):
        """Refresh the current page - simple and reliable"""
        try:
            # Method 1: Get current URL and revisit (most reliable)
            current_url = self.get_current_url()
            print(f"[Thread-{self.thread_id}] Refreshing page: {current_url}")
            self.open(current_url)
            time.sleep(random.uniform(2, 3))
            print(f"[Thread-{self.thread_id}] Page refreshed successfully")
            return True
            
        except Exception as e:
            print(f"[Thread-{self.thread_id}] Method 1 failed, trying browser refresh: {e}")
            
            # Method 2: Use driver.refresh() as fallback
            try:
                self.driver.refresh()
                time.sleep(random.uniform(2, 3))
                print(f"[Thread-{self.thread_id}] Browser refresh successful")
                return True
            except Exception as e2:
                print(f"[Thread-{self.thread_id}] Method 2 failed, trying JavaScript reload: {e2}")
                
                # Method 3: JavaScript reload as last resort
                try:
                    self.execute_script("location.reload(true);")
                    time.sleep(random.uniform(2, 3))
                    print(f"[Thread-{self.thread_id}] JavaScript reload successful")
                    return True
                except Exception as e3:
                    print(f"[Thread-{self.thread_id}] All refresh methods failed: {e3}")
                    return False

    def is_retryable_error(self, error_type):
        """Check if error type is retryable"""
        return error_type in RETRYABLE_ERROR_TYPES

    def collect_session_info(self, context=""):
        """Collect basic session information"""
        try:
            js_info = self.execute_script("""
                (function() {
                    try {
                        return {
                            userAgent: (navigator && navigator.userAgent) || '',
                            screenWidth: (typeof screen !== 'undefined' && screen.width) || '',
                            screenHeight: (typeof screen !== 'undefined' && screen.height) || '',
                            timezone: (typeof Intl !== 'undefined' && Intl.DateTimeFormat().resolvedOptions().timeZone) || '',
                            language: (navigator && navigator.language) || ''
                        };
                    } catch (e) {
                        return {};
                    }
                })();
            """) or {}

            session_info = {
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'browser': self.browser_type,
                'thread_id': self.thread_id,
                'session_duration': (datetime.now() - self.session_start).total_seconds(),
                **js_info
            }

            fingerprint_data = f"{js_info.get('userAgent', '')}{js_info.get('screenWidth', '')}{js_info.get('timezone', '')}"
            session_info['fingerprint'] = hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]

            return session_info
        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error collecting session info: {e}")
            return {'timestamp': datetime.now().isoformat(), 'browser': self.browser_type, 'thread_id': self.thread_id, 'error': str(e)}

    def parse_date(self, date_str):
        """Parse MM/DD/YY or MM/DD/YYYY date format"""
        try:
            if not date_str:
                return None

            if '-' in date_str:
                date_str = date_str.split('-')[-1].strip()

            month, day, year = map(int, date_str.split("/"))

            if year < 100:
                year = 2000 + year if year < 50 else 1900 + year

            return date(year, month, day)
        except:
            return None

    def subtract_months(self, d, months):
        """Subtract months from date"""
        year = d.year
        month = d.month - months

        while month <= 0:
            month += 12
            year -= 1

        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(d.day, last_day))

    def is_company(self, name: str) -> bool:
        """Check if name is a company"""
        if not name:
            return True
        n = " ".join(name.split()).strip()
        u = n.upper()
        bad_words = [
            " LLC"," INC"," LLP"," LTD"," PLLC"," P.L.L.C"," P.C."," PC"," CORP"," CORPORATION",
            " MEDICAL CENTER"," CENTER"," CLINIC"," GROUP"," ASSOCIATES"," ASSOC",
            " HOSPITAL"," HEALTH"," CARE"," SERVICES"," SERVICE"," URGENT CARE",
            " IMAGING"," LAB"," LABORATORY"," DIAGNOSTIC"," RADIOLOGY"," PHARMACY",
            " EQUIPMENT"," SUPPLY"," IPA"," ASC"," SURGICAL"," OUTPATIENT"," INPATIENT"
        ]
        if any(k in u for k in bad_words):
            return True
        if any(ch.isdigit() for ch in u):
            return True

        name_chars = re.sub(r'[^A-Z\s\'-]', '', u)

        if re.match(r"^[A-Z'\-]+,\s*[A-Z'\-]+(\s+[A-Z'\-]+)?(\s*(MD|DO|DDS|DPM|OD|NP|PA|RN))?$", u):
            return False

        if re.match(r"^[A-Z][a-z'\-]+\s+[A-Z][a-z'\-]+(\s+[A-Z][a-z'\-]+)?(\s*(MD|DO|DDS|DPM|OD|NP|PA|RN))?$", n):
            return False

        if "," in u:
            left, right = u.split(",", 1)
            left_clean = left.strip()
            right_clean = right.strip()

            if (left_clean and right_clean and
                re.match(r"^[A-Z'\-\s]+$", left_clean) and
                re.match(r"^[A-Z'\-\s]+(MD|DO|DDS|DPM|OD|NP|PA|RN)?$", right_clean.split()[0] if right_clean.split() else "")):
                return False

        return True

    def safe_sleep(self, delay_range=None):
        """Random sleep with anti-bot measures"""
        if delay_range is None:
            delay = self.anti_bot.randomize_delays()
        else:
            delay = random.uniform(*delay_range)
        time.sleep(delay)

    def wait_for_element_present(self, selector, timeout=10):
        """Wait for element to be present in DOM"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                elements = self.find_elements(selector)
                if elements:
                    return True
            except:
                pass
            self.sleep(0.3)
        return False

    def wait_for_element_visible_improved(self, selector, timeout=10):
        """Improved element visibility waiting with anti-bot checks"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                elements = self.find_elements(selector)
                for element in elements:
                    if element.is_displayed():
                        if random.random() > 0.7:
                            self.anti_bot.random_mouse_movement(self.driver)
                        return True
            except:
                pass
            self.sleep(0.3)
        return False

    def is_captcha_present(self, timeout=5):
        """Delegate to improved handler"""
        return self.captcha_handler.is_captcha_present(timeout)

    def solve_captcha(self):
        """Delegate to improved handler"""
        return self.captcha_handler.solve_captcha()

    def handle_2fa(self, timeout=10):
        """Detects and handles a 2FA page"""
        print(f"[Thread-{self.thread_id}] Checking for 2FA page...")

        two_fa_indicators = [
            "h1:contains('Verify your identity')",
            "p:contains('enter the code we sent to')",
            "input[name='securityCode']",
            "#mfa-code-input"
        ]

        for indicator in two_fa_indicators:
            if self.wait_for_element_present(indicator):
                print(f"[Thread-{self.thread_id}] 2FA page detected")
                return True, "2FA_REQUIRED", "Account requires 2FA, cannot proceed."

        return False, "", ""

    def is_text_present(self, text, timeout=3):
        """Checks if the given text is visible on the page"""
        try:
            self.wait_for_text(text, timeout=timeout)
            return True
        except:
            return False

    def verify_field_value(self, selector, expected_value, timeout=5):
        """Verify field has expected value"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                element = self.find_element(selector)
                actual_value = self.execute_script("return arguments[0].value;", element)
                if actual_value == expected_value:
                    return True
            except:
                pass
            time.sleep(0.3)
        return False

    def attempt_login(self, username, password, max_retries=5):
        """Updated login with robust username/password input handling"""
        
        try:
            # Navigate to FRESH login page with cache clearing
            self.delete_all_cookies()
            try:
                self.execute_script("window.sessionStorage.clear(); window.localStorage.clear();")
            except:
                pass
            
            self.open("https://www.medicare.gov/account/login")
            self.sleep(2)  # Reduced from 3

            if not self.wait_for_element_visible_improved('input[name="username"]', timeout=15):
                return False, "PAGE_LOAD_FAILED", "Username field not found"

            # ============== IMPROVED USERNAME INPUT ==============
            username_success = False
            for input_attempt in range(3):
                try:
                    username_field = self.find_element('input[name="username"]')
                    
                    # Clear and set value
                    self.execute_script("""
                        var field = arguments[0];
                        field.value = '';
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                    """, username_field)
                    self.sleep(0.2)
                    
                    username_field.clear()
                    self.sleep(0.1)
                    username_field.click()
                    self.sleep(0.1)
                    
                    # Set value using JavaScript
                    self.execute_script("""
                        var field = arguments[0];
                        var text = arguments[1];
                        field.focus();
                        field.value = text;
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                        field.dispatchEvent(new Event('change', { bubbles: true }));
                    """, username_field, username)
                    self.sleep(0.3)
                    
                    # Verify
                    entered_username = self.execute_script("return arguments[0].value;", username_field)
                    
                    if entered_username == username:
                        username_success = True
                        break
                    else:
                        self.sleep(0.5)
                        
                except Exception as e:
                    self.sleep(0.5)
            
            if not username_success:
                # Last resort: reload and try once more
                self.open("https://www.medicare.gov/account/login")
                self.sleep(2)
                
                username_field = self.find_element('input[name="username"]')
                self.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                """, username_field, username)
                self.sleep(0.5)
                
                entered_username = self.execute_script("return arguments[0].value;", username_field)
                if entered_username != username:
                    return False, "USERNAME_INPUT_FAILED", f"Could not enter username"
            
            # ============== CLICK SUBMIT TO GO TO PASSWORD PAGE ==============
            try:
                self.click('button[type="submit"]')
            except:
                # Try finding submit button by text
                try:
                    submit_btn = self.find_element('xpath=//button[contains(text(), "Continue") or contains(text(), "Next")]')
                    submit_btn.click()
                except:
                    pass
            
            self.sleep(2)

            # Wait longer and try multiple times for password field
            password_field_found = False
            for wait_attempt in range(3):
                if self.wait_for_element_visible_improved('input[name="password"]', timeout=8):
                    password_field_found = True
                    break
                else:
                    # Might still be on username page, try clicking submit again
                    if wait_attempt < 2:
                        try:
                            self.click('button[type="submit"]')
                            self.sleep(2)
                        except:
                            pass
            
            if not password_field_found:
                return False, "PAGE_LOAD_FAILED", "Password field not found after multiple attempts"

            # ============== IMPROVED PASSWORD INPUT ==============
            password_success = False
            for input_attempt in range(3):
                try:
                    password_field = self.find_element('input[name="password"]')
                    
                    # Clear and set password
                    self.execute_script("""
                        var field = arguments[0];
                        field.value = '';
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                    """, password_field)
                    self.sleep(0.1)
                    
                    password_field.clear()
                    self.sleep(0.1)
                    password_field.click()
                    self.sleep(0.1)
                    
                    # Set password using JavaScript
                    self.execute_script("""
                        var field = arguments[0];
                        var text = arguments[1];
                        field.focus();
                        field.value = text;
                        field.dispatchEvent(new Event('input', { bubbles: true }));
                        field.dispatchEvent(new Event('change', { bubbles: true }));
                    """, password_field, password)
                    self.sleep(0.3)
                    
                    # Verify (without reading password for security)
                    has_value = self.execute_script("return arguments[0].value.length > 0;", password_field)
                    if has_value:
                        password_success = True
                        break
                    else:
                        self.sleep(0.5)
                        
                except Exception as e:
                    self.sleep(0.5)
            
            if not password_success:
                return False, "PASSWORD_INPUT_FAILED", "Could not enter password"

            # ============== REST OF LOGIN LOGIC ==============
            for attempt in range(max_retries):
                button_clicked = False
                try:
                    login_button_xpath_1 = '//*[@id="App"]/div/div/div[1]/div[1]/div/div[2]/form/div[4]/button[1]'
                    self.click(login_button_xpath_1)
                    button_clicked = True
                except:
                    try:
                        login_button_xpath_2 = '//*[@id="App"]/div/div/div[1]/div[1]/div/div[3]/form/div[4]/button[1]'
                        self.click(login_button_xpath_2)
                        button_clicked = True
                    except:
                        # Try generic submit button
                        try:
                            self.click('button[type="submit"]')
                            button_clicked = True
                        except:
                            pass

                if not button_clicked:
                    return False, "LOGIN_BUTTON_FAILED", "Login button not found"

                self.sleep(2)  # Reduced from 3
                if not self.captcha_handler.monitor_and_solve_if_present("immediate_after_login"):
                    return False, "CAPTCHA_FAILED", "Failed to solve CAPTCHA"

                current_url = self.get_current_url()
                if "/account/security-code/" in current_url:
                    return False, "2FA_DETECTED", "2FA required"

                if self.is_text_present("we can't process your request at this time"):
                    continue

                success, error_type, error_msg = self.wait_for_login_completion(timeout=LOGIN_TIMEOUT)

                if success:
                    if not self.captcha_handler.monitor_and_solve_if_present("login_success_page"):
                        return False, "CAPTCHA_FAILED", "CAPTCHA on post-login page"

                    return True, "", ""

                if error_type not in ["SYSTEM_ERROR", "RATE_LIMITED", "LOGIN_TIMEOUT"]:
                    return False, error_type, error_msg

            return False, "LOGIN_FAILED", "Max retries reached"

        except Exception as e:
            return False, "LOGIN_EXCEPTION", str(e)

    def detect_login_error(self, timeout=ERROR_DETECTION_TIMEOUT):
        """Enhanced error detection with rate limiting check"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                error_selectors = [
                    ".ds-c-alert--error",
                    ".ds-c-alert__body",
                    ".ds-c-alert__heading"
                ]

                for selector in error_selectors:
                    elements = self.find_elements(selector)
                    for element in elements:
                        if element.is_displayed():
                            error_text = element.text.strip().lower()
                            print(f"[Thread-{self.thread_id}] Found error: {error_text[:100]}")

                            for error_type, patterns in ERROR_PATTERNS.items():
                                if any(pattern.lower() in error_text for pattern in patterns):
                                    return True, error_type, error_text

                            if selector == ".ds-c-alert--error":
                                return True, "GENERAL_ERROR", error_text

                success_selectors = [
                    'a[href="/my/claims"]',
                    'a[aria-label*="Check my claims"]',
                    'button[aria-label*="Show my claims"]'
                ]

                for selector in success_selectors:
                    if self.wait_for_element_visible_improved(selector, timeout=1):
                        return False, "", ""

            except Exception as e:
                print(f"[Thread-{self.thread_id}] Error detection check failed: {e}")

            self.sleep(0.5)

        return False, "", ""

    def wait_for_login_completion(self, timeout=LOGIN_TIMEOUT):
        """Enhanced login completion check with rate limiting detection"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.is_captcha_present(timeout=2):
                    if not self.solve_captcha():
                        return False, "CAPTCHA_FAILED", "Failed to solve CAPTCHA during login wait"
                    self.sleep(3)

                error_elements = self.find_elements(".ds-c-alert--error")
                for element in error_elements:
                    if element.is_displayed():
                        error_text = element.text.strip().lower()
                        print(f"[Thread-{self.thread_id}] Login error: {error_text[:100]}")

                        if "can't process your request at this time" in error_text:
                            return False, "RATE_LIMITED", error_text

                        for error_type, patterns in ERROR_PATTERNS.items():
                            if any(pattern.lower() in error_text for pattern in patterns):
                                return False, error_type, error_text

                        return False, "GENERAL_ERROR", error_text

                success_selectors = [
                    'a[href="/my/claims"]',
                    'a[aria-label*="Check my claims"]',
                    'button[aria-label*="Show my claims"]',
                    '.m-c-card'
                ]

                for selector in success_selectors:
                    if self.wait_for_element_visible_improved(selector, timeout=1):
                        return True, "", ""

                current_url = self.get_current_url()
                if "/my/" in current_url and "/login" not in current_url:
                    return True, "", ""

            except Exception as e:
                print(f"[Thread-{self.thread_id}] Login completion check error: {e}")

            self.sleep(0.5)

        current_url = self.get_current_url()
        if "/login" in current_url:
            return False, "LOGIN_TIMEOUT", "Still on login page after timeout"
        else:
            return True, "", "Assumed success"

    def evaluate_doctor_by_name_and_state(self, doctor_name, state):
        """Updated to use taxonomy-based evaluation system with detailed return data"""
        try:
            providers = self.npi_service.search_providers(doctor_name, state, max_results=1)

            if not providers:
                return None

            provider = providers[0]

            validation_result = self.npi_service.validate_provider_basic_criteria(provider)
            if not validation_result['isValid']:
                return None

            taxonomy_evaluation = self.specialty_validator.evaluate_provider_by_taxonomy(provider)

            npi = provider.get('npi', '')
            enrollment_status = "Unknown"
            is_enrolled = None

            if npi:
                enrollment_result = self.pecos_service.check_provider_enrollment(npi)
                is_enrolled = enrollment_result.get('isEnrolled')
                if is_enrolled:
                    enrollment_status = "Enrolled"
                elif is_enrolled is False:
                    enrollment_status = "Not Enrolled"

            decision_result = self.make_taxonomy_decision(taxonomy_evaluation, enrollment_status, is_enrolled)

            if not decision_result['accept']:
                return None

            doctor_info = {
                'provider': provider.get('fullName', doctor_name),
                'address': f"{provider.get('practiceAddress', '')}, {provider.get('practiceCity', '')}, {provider.get('practiceState', '')} {provider.get('practiceZip', '')}".strip(", "),
                'npi': npi,
                'enrollment': enrollment_status,
                'specialty': provider.get('primaryTaxonomyName', ''),
                'taxonomyCode': provider.get('primaryTaxonomyCode', ''),
                'phone': provider.get('practicePhone', ''),
                'source': 'DR_EVALUATION',
                'acceptanceReason': decision_result['reason'],
                'evaluationMethod': taxonomy_evaluation['evaluation_method'],
                'isCnEligible': decision_result['is_cn_eligible']
            }

            return doctor_info

        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error evaluating doctor: {e}")
            return None

    def make_taxonomy_decision(self, taxonomy_evaluation, enrollment_status, is_enrolled):
        """Make decision based on taxonomy evaluation and enrollment"""
        result = {
            'accept': False,
            'reason': '',
            'is_cn_eligible': False,
            'category': 'OTHER_FAILED'
        }

        if taxonomy_evaluation['category'] == 'GOOD':
            if enrollment_status in ["Enrolled", "Unknown"]:
                result['accept'] = True
                result['reason'] = f"Good taxonomy: {taxonomy_evaluation['taxonomy_code']}"
                result['category'] = 'GOOD'
            else:
                result['reason'] = f"Good taxonomy but not enrolled in PECOS"
                result['category'] = 'NOT_ENROLLED'

        elif taxonomy_evaluation['category'] == 'BAD':
            if taxonomy_evaluation['is_cn_eligible']:
                result['accept'] = True
                result['reason'] = f"Bad taxonomy but good for CN: {taxonomy_evaluation['taxonomy_code']}"
                result['is_cn_eligible'] = True
                result['category'] = 'CN_ELIGIBLE'
            else:
                result['reason'] = f"Bad taxonomy: {taxonomy_evaluation['taxonomy_code']}"
                result['category'] = 'BAD_SPECIALTY'

        elif taxonomy_evaluation['category'] == 'CN_ELIGIBLE':
            result['accept'] = True
            result['reason'] = f"Good for CN: {taxonomy_evaluation['reason']}"
            result['is_cn_eligible'] = True
            result['category'] = 'CN_ELIGIBLE'

        else:
            if enrollment_status == "Enrolled":
                result['accept'] = True
                result['reason'] = f"Unknown taxonomy but enrolled: {taxonomy_evaluation['taxonomy_code']}"
                result['category'] = 'GOOD'
            else:
                result['reason'] = f"Unknown taxonomy and not enrolled: {taxonomy_evaluation['taxonomy_code']}"
                result['category'] = 'OTHER_FAILED'

        return result

    def determine_failure_reason(self, provider_name, state):
        """Determine specific failure reason for a provider using taxonomy-based system"""
        try:
            providers = self.npi_service.search_providers(provider_name, state, max_results=1)

            if not providers:
                return "Not found in NPI Registry"

            provider = providers[0]

            validation_result = self.npi_service.validate_provider_basic_criteria(provider)
            if not validation_result['isValid']:
                return f"Provider validation failed: {', '.join(validation_result['reasons'])}"

            taxonomy_evaluation = self.specialty_validator.evaluate_provider_by_taxonomy(provider)

            npi = provider.get('npi', '')
            enrollment_status = "Unknown"

            if npi:
                enrollment_result = self.pecos_service.check_provider_enrollment(npi)
                if enrollment_result.get('isEnrolled'):
                    enrollment_status = "Enrolled"
                elif enrollment_result.get('isEnrolled') is False:
                    enrollment_status = "Not Enrolled"

            if taxonomy_evaluation['category'] == 'GOOD':
                if enrollment_status == "Not Enrolled":
                    return f"Good taxonomy but not enrolled in PECOS (Taxonomy: {taxonomy_evaluation['taxonomy_code']})"
                else:
                    return "Unknown error - should have been approved (Good taxonomy)"

            elif taxonomy_evaluation['category'] == 'BAD':
                if taxonomy_evaluation['is_cn_eligible']:
                    return "Unknown error - should have been approved (Bad taxonomy but good for CN)"
                else:
                    return f"Bad taxonomy: {taxonomy_evaluation['taxonomy_code']}"

            elif taxonomy_evaluation['category'] == 'CN_ELIGIBLE':
                return "Unknown error - should have been approved (Good for CN)"

            else:
                if enrollment_status == "Enrolled":
                    return "Unknown error - should have been approved (Unknown taxonomy but enrolled)"
                else:
                    return f"Unknown taxonomy ({taxonomy_evaluation['taxonomy_code']}) and not enrolled in PECOS"

        except Exception as e:
            return f"Error determining failure reason: {str(e)}"

    def navigate_to_claims(self):
        """Navigate to claims page"""
        try:
            claims_selectors = [
                'a[href="/my/claims"]',
                'a[aria-label*="Check my claims"]',
                'button[aria-label*="Show my claims"]'
            ]

            clicked = False
            for selector in claims_selectors:
                if self.wait_for_element_visible_improved(selector, timeout=5):
                    self.click(selector)
                    clicked = True
                    break

            if not clicked:
                self.open("https://www.medicare.gov/my/claims")

            self.sleep(2)  # Reduced from 3

            if "/my/claims" not in self.get_current_url():
                self.open("https://www.medicare.gov/my/claims")

            return self.wait_for_claims_loaded()

        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error navigating: {e}")
            return False

    def wait_for_claims_loaded(self):
        """Wait for claims page to fully load"""
        start_time = time.time()
        while time.time() - start_time < CLAIMS_LOAD_TIMEOUT:
            try:
                cards = self.find_elements('.m-c-card')
                if len(cards) > 0:
                    self.sleep(1)  # Reduced from 2
                    return True

                no_claims_selectors = [
                    "text='No claims found'",
                    "text='You have no claims'",
                    ".no-claims-message"
                ]

                for selector in no_claims_selectors:
                    if self.wait_for_element_visible_improved(selector, timeout=1):
                        return True

            except:
                pass

            self.sleep(1)

        return False

    def extract_card_basic_info(self, card):
        """Extract basic info from claim card without entering it"""
        try:
            card_text = card.text

            date_patterns = [
                r'Date of service[:\s]*(\d{2}/\d{2}/\d{2,4})',
                r'Service date[:\s]*(\d{2}/\d{2}/\d{2,4})',
                r'(\d{2}/\d{2}/\d{2,4})'
            ]

            date_text = ""
            for pattern in date_patterns:
                date_match = re.search(pattern, card_text, re.IGNORECASE)
                if date_match:
                    date_text = date_match.group(1)
                    break

            provider_patterns = [
                r'Provider[:\s]*([A-Z][A-Z\s,\'-\.]+?)(?:\n|$|Date|Amount)',
                r'([A-Z][A-Z\s,\'-\.]+?)(?:\s*\n.*?Provider address|\s*\n.*?Date of service)',
                r'([A-Z]+,\s*[A-Z]+[A-Z\s\'-]*)'
            ]

            provider_text = ""
            for pattern in provider_patterns:
                provider_match = re.search(pattern, card_text, re.IGNORECASE | re.MULTILINE)
                if provider_match:
                    provider_text = provider_match.group(1).strip()
                    provider_text = re.sub(r'\s+', ' ', provider_text)
                    if len(provider_text) > 5:
                        break

            return {
                'date': date_text,
                'provider': provider_text,
                'card_text': card_text
            }
        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error extracting card: {e}")
            return {'date': "", 'provider': "", 'card_text': ""}

    def load_more_claims(self):
        """Load more claims if available"""
        try:
            self.scroll_to_bottom()
            self.sleep(0.5)  # Reduced from 1

            load_more_selectors = [
                'button.ds-c-button.ds-u-margin-top--4',
                'xpath=//button[contains(text(), "Load more claims")]',
                'xpath=//button[contains(text(), "Show more")]'
            ]

            for selector in load_more_selectors:
                try:
                    if selector.startswith('xpath='):
                        elements = self.find_elements(selector[6:], by="xpath")
                    else:
                        elements = self.find_elements(selector)

                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text.strip().lower()
                            if any(phrase in element_text for phrase in ['load more', 'show more', 'more claims']):
                                self.execute_script("arguments[0].click();", element)
                                self.sleep(1.5)  # Reduced from 2
                                return True

                except Exception as e:
                    continue

            return False

        except Exception as e:
            return False

    def get_all_claim_cards_basic_info(self, patient_state):
        """Get basic info from all claim cards with early termination"""
        threshold_date = self.subtract_months(date.today(), 9)
        all_claims = []
        processed_providers = set()
        should_continue_loading = True

        while should_continue_loading:
            try:
                cards = self.find_elements('.m-c-card')
                current_card_count = len(cards)

                for i, card in enumerate(cards):
                    if i >= len(all_claims):
                        card_info = self.extract_card_basic_info(card)
                        date_str = card_info['date']
                        provider_name = card_info['provider']

                        if not date_str:
                            continue

                        claim_date = self.parse_date(date_str)
                        if not claim_date:
                            continue

                        if claim_date < threshold_date:
                            should_continue_loading = False
                            break

                        if self.is_company(provider_name):
                            continue

                        provider_key = provider_name.upper().strip()
                        if provider_key in processed_providers:
                            continue

                        processed_providers.add(provider_key)

                        card_info['card_index'] = i
                        card_info['dateOfService'] = claim_date.strftime("%m/%d/%Y")
                        all_claims.append(card_info)

                if should_continue_loading:
                    if not self.load_more_claims():
                        break

                    new_cards = self.find_elements('.m-c-card')
                    if len(new_cards) <= current_card_count:
                        break
                    else:
                        self.sleep(2)  # Reduced from 3

            except Exception as e:
                break

        return all_claims

    def click_claim_details(self, card_index, max_attempts=3):
        """Click claim details button with retry logic"""
        for attempt in range(max_attempts):
            try:
                cards = self.find_elements('.m-c-card')
                if card_index >= len(cards):
                    return False

                card = cards[card_index]

                self.execute_script("""
                    arguments[0].scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                """, card)
                self.sleep(0.5)  # Reduced from 1

                detail_button_selectors = [
                    ".//a[contains(@aria-label, 'Open claim details')]",
                    ".//a[contains(text(), 'Open Claim Details')]",
                    ".//a[contains(@class, 'ds-c-button')]"
                ]

                detail_button = None
                for selector in detail_button_selectors:
                    try:
                        detail_button = card.find_element("xpath", selector)
                        if detail_button.is_displayed():
                            break
                    except:
                        continue

                if not detail_button:
                    return False

                current_url = self.get_current_url()
                self.execute_script("arguments[0].click();", detail_button)
                self.sleep(1.5)  # Reduced from 2

                start_time = time.time()
                while time.time() - start_time < DETAIL_TIMEOUT:
                    new_url = self.get_current_url()
                    if new_url != current_url and "/claims/" in new_url:
                        self.sleep(1)  # Reduced from 2
                        return True
                    self.sleep(0.5)

            except Exception as e:
                self.sleep(1)  # Reduced from 2

        return False

    def extract_complete_claim_details(self):
        """Extract COMPLETE claim details including all services and financial data"""
        try:
            claim_data = {
                'basic_info': {},
                'services': [],
                'summary': {},
                'raw_html': ''
            }
            
            # === BASIC INFO SECTION ===
            # Date of service
            try:
                date_elem = self.find_element("xpath=//div[contains(text(), 'Date of service')]/following-sibling::div")
                claim_data['basic_info']['date_of_service'] = date_elem.text.strip()
            except:
                claim_data['basic_info']['date_of_service'] = ''
            
            # Provider name
            try:
                provider_elem = self.find_element("xpath=//div[contains(text(), 'Provider')]/following-sibling::div")
                claim_data['basic_info']['provider'] = provider_elem.text.strip()
            except:
                claim_data['basic_info']['provider'] = ''
            
            # Provider address
            try:
                address_elem = self.find_element("xpath=//div[contains(text(), 'Provider address')]/following-sibling::div")
                address_lines = address_elem.find_elements("xpath", ".//div")
                if address_lines:
                    address_parts = [line.text.strip() for line in address_lines if line.text.strip()]
                    claim_data['basic_info']['provider_address'] = ', '.join(address_parts)
                else:
                    claim_data['basic_info']['provider_address'] = address_elem.text.strip()
            except:
                claim_data['basic_info']['provider_address'] = ''
            
            # Claim processed on
            try:
                processed_elem = self.find_element("xpath=//div[contains(text(), 'Claim processed on')]/following-sibling::div")
                claim_data['basic_info']['claim_processed_on'] = processed_elem.text.strip()
            except:
                claim_data['basic_info']['claim_processed_on'] = ''
            
            # Practicing providers
            try:
                practicing_elem = self.find_element("xpath=//div[contains(text(), 'Practicing providers')]/following-sibling::div")
                claim_data['basic_info']['practicing_providers'] = practicing_elem.text.strip()
            except:
                claim_data['basic_info']['practicing_providers'] = ''
            
            # Claim number (from Order MSN dialog if available)
            try:
                claim_number_elem = self.find_element("xpath=//h3[contains(text(), 'Claim number')]/following-sibling::div")
                claim_data['basic_info']['claim_number'] = claim_number_elem.text.strip()
            except:
                claim_data['basic_info']['claim_number'] = ''
            
            # === SERVICES SECTION ===
            try:
                service_containers = self.find_elements("css selector=._container_uudit_1")
                
                for container in service_containers:
                    try:
                        service = {}
                        
                        # Service name and procedure code
                        try:
                            service_elem = container.find_element("xpath", ".//div[contains(text(), 'Service (procedure code)')]/following-sibling::div")
                            service_text = service_elem.text.strip()
                            # Parse "SERVICE NAME (CODE)" format
                            if '(' in service_text and ')' in service_text:
                                service['service_name'] = service_text[:service_text.rfind('(')].strip()
                                service['procedure_code'] = service_text[service_text.rfind('(')+1:service_text.rfind(')')].strip()
                            else:
                                service['service_name'] = service_text
                                service['procedure_code'] = ''
                        except:
                            service['service_name'] = ''
                            service['procedure_code'] = ''
                        
                        # Quantity
                        try:
                            qty_elem = container.find_element("xpath", ".//div[contains(text(), 'Qty')]/following-sibling::div")
                            service['quantity'] = qty_elem.text.strip()
                        except:
                            service['quantity'] = ''
                        
                        # Provider charged
                        try:
                            charged_elem = container.find_element("xpath", ".//div[contains(text(), 'Provider charged')]/following-sibling::div")
                            service['provider_charged'] = charged_elem.text.strip()
                        except:
                            service['provider_charged'] = ''
                        
                        # Medicare approved
                        try:
                            approved_elem = container.find_element("xpath", ".//div[contains(text(), 'Medicare approved')]/following-sibling::div")
                            service['medicare_approved'] = approved_elem.text.strip()
                        except:
                            service['medicare_approved'] = ''
                        
                        # Applied to deductible
                        try:
                            deductible_elem = container.find_element("xpath", ".//div[contains(text(), 'Applied to deductible')]/following-sibling::div")
                            service['applied_to_deductible'] = deductible_elem.text.strip()
                        except:
                            service['applied_to_deductible'] = ''
                        
                        # Coinsurance
                        try:
                            coinsurance_elem = container.find_element("xpath", ".//div[contains(text(), 'Coinsurance')]/following-sibling::div")
                            service['coinsurance'] = coinsurance_elem.text.strip()
                        except:
                            service['coinsurance'] = ''
                        
                        # You may be billed
                        try:
                            billed_elem = container.find_element("xpath", ".//div[contains(text(), 'You may be billed')]/following-sibling::div")
                            service['you_may_be_billed'] = billed_elem.text.strip()
                        except:
                            service['you_may_be_billed'] = ''
                        
                        if service.get('service_name') or service.get('procedure_code'):
                            claim_data['services'].append(service)
                        
                    except Exception as e:
                        continue
            except:
                pass
            
            # === SUMMARY SECTION ===
            summary_fields = [
                ('Total amount charged', 'total_amount_charged'),
                ('Total Medicare approved', 'total_medicare_approved'),
                ('Blood deductible', 'blood_deductible'),
                ('Physical therapy charges', 'physical_therapy_charges'),
                ('Psychiatric charges', 'psychiatric_charges'),
                ('Occupational therapy charges', 'occupational_therapy_charges'),
                ('Total patient paid the provider', 'total_patient_paid_provider'),
                ('Total Medicare paid you', 'total_medicare_paid_you'),
                ('Total Medicare paid the provider', 'total_medicare_paid_provider'),
                ('Total applied to deductible', 'total_applied_to_deductible'),
                ('Total coinsurance', 'total_coinsurance'),
                ('Total you may be billed', 'total_you_may_be_billed')
            ]
            
            for display_name, field_name in summary_fields:
                try:
                    elem = self.find_element(f"xpath=//h3[contains(text(), '{display_name}')]/following-sibling::div")
                    claim_data['summary'][field_name] = elem.text.strip()
                except:
                    claim_data['summary'][field_name] = ''
            
            return claim_data
            
        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error extracting complete claim: {e}")
            return {'basic_info': {}, 'services': [], 'summary': {}}
    
    def extract_provider_details(self):
        """Extract provider details from claim details page (LEGACY - kept for compatibility)"""
        try:
            provider_info = {'provider': '', 'address': ''}

            detail_selectors = [
                "//div[contains(text(), 'Provider')]/following-sibling::div",
                "//div[@class='ds-text-body--md ds-u-margin--0'][contains(text(), 'Provider')]/following-sibling::div",
                ".ds-text-heading--lg"
            ]

            for selector in detail_selectors:
                try:
                    elements = self.find_elements("xpath", selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 2 and not re.match(r'^\d{2}/\d{2}/\d{2,4}', text):
                            if re.match(r'^[A-Z][A-Z\s,\'-]+', text) or ',' in text:
                                provider_info['provider'] = text
                                break
                    if provider_info['provider']:
                        break
                except:
                    continue

            address_selectors = [
                "//div[contains(text(), 'Provider address')]/following-sibling::div",
                "//div[@class='ds-text-body--md ds-u-margin--0'][contains(text(), 'Provider address')]/following-sibling::div"
            ]

            for selector in address_selectors:
                try:
                    address_elements = self.find_elements("xpath", selector)
                    if address_elements:
                        address_element = address_elements[0]
                        address_lines = address_element.find_elements("xpath", ".//div")
                        if address_lines:
                            address_parts = [line.text.strip() for line in address_lines if line.text.strip()]
                            if address_parts:
                                provider_info['address'] = ', '.join(address_parts)
                        else:
                            provider_info['address'] = address_element.text.strip()

                        if provider_info['address']:
                            break
                except:
                    continue

            return provider_info

        except Exception as e:
            print(f"[Thread-{self.thread_id}] Error extracting: {e}")
            return {'provider': '', 'address': ''}

    def navigate_back_to_claims(self):
        """Navigate back to claims list"""
        try:
            back_selectors = [
                "xpath=//a[contains(text(), 'Back to claims')]",
                "xpath=//button[contains(text(), 'Back')]",
                "xpath=//a[contains(@aria-label, 'Back to')]"
            ]

            for selector in back_selectors:
                try:
                    if self.wait_for_element_visible_improved(selector, timeout=3):
                        self.click(selector)
                        self.sleep(2)  # Reduced from 3

                        if "/my/claims" in self.get_current_url() and "/my/claims/" not in self.get_current_url():
                            self.wait_for_claims_loaded()
                            return True
                except:
                    continue

            self.go_back()
            self.sleep(2)  # Reduced from 3

            if "/my/claims" in self.get_current_url() and "/my/claims/" not in self.get_current_url():
                self.wait_for_claims_loaded()
                return True

            self.open("https://www.medicare.gov/my/claims")
            return self.wait_for_claims_loaded()

        except Exception as e:
            return False

    def process_claims_with_taxonomy_evaluation(self, all_claims, patient_state):
        """Process claims using taxonomy-based DR evaluation"""
        good_providers = []
        cn_providers = []
        dr_suggestions = {
            'bad_specialty': [],
            'not_found': [],
            'not_enrolled': [],
            'other_failed': []
        }

        for i, claim in enumerate(all_claims):
            provider_name = claim['provider']

            doctor_info = self.evaluate_doctor_by_name_and_state(provider_name, patient_state)

            if doctor_info:
                doctor_info['dateOfService'] = claim['dateOfService']

                if doctor_info.get('isCnEligible', False):
                    cn_providers.append(doctor_info)
                else:
                    good_providers.append(doctor_info)
            else:
                if self.click_claim_details(claim['card_index']):
                    detailed_info = self.extract_provider_details()

                    if detailed_info['provider'] and detailed_info['address']:
                        dr_state = self.npi_service.extract_state_from_address(detailed_info['address'])

                        if dr_state and dr_state != patient_state:
                            doctor_info = self.evaluate_doctor_by_name_and_state(detailed_info['provider'], dr_state)

                            if doctor_info:
                                doctor_info['dateOfService'] = claim['dateOfService']
                                doctor_info['source'] = 'DETAILED_EXTRACTION'

                                if doctor_info.get('isCnEligible', False):
                                    cn_providers.append(doctor_info)
                                else:
                                    good_providers.append(doctor_info)
                            else:
                                self.categorize_failed_provider(
                                    detailed_info['provider'],
                                    detailed_info['address'],
                                    claim['dateOfService'],
                                    dr_state or patient_state,
                                    dr_suggestions
                                )
                        else:
                            self.categorize_failed_provider(
                                detailed_info['provider'],
                                detailed_info['address'],
                                claim['dateOfService'],
                                patient_state,
                                dr_suggestions
                            )
                    else:
                        suggestion = {
                            'provider': provider_name,
                            'address': 'Could not extract',
                            'dateOfService': claim['dateOfService'],
                            'reason': 'Failed extraction'
                        }
                        dr_suggestions['other_failed'].append(suggestion)

                    if not self.navigate_back_to_claims():
                        break
                    self.sleep(1)  # Reduced from 2
                else:
                    suggestion = {
                        'provider': provider_name,
                        'address': 'Could not access',
                        'dateOfService': claim['dateOfService'],
                        'reason': 'Failed to open details'
                    }
                    dr_suggestions['other_failed'].append(suggestion)

        return good_providers, cn_providers, dr_suggestions

    def categorize_failed_provider(self, provider_name, address, date_of_service, state, dr_suggestions):
        """Categorize failed provider based on failure reason"""
        try:
            failure_reason = self.determine_failure_reason(provider_name, state)

            suggestion = {
                'provider': provider_name,
                'address': address,
                'dateOfService': date_of_service,
                'reason': failure_reason
            }

            if "not found" in failure_reason.lower():
                dr_suggestions['not_found'].append(suggestion)
                category = "NOT_FOUND"
            elif "not enrolled" in failure_reason.lower():
                dr_suggestions['not_enrolled'].append(suggestion)
                category = "NOT_ENROLLED"
            elif "bad taxonomy" in failure_reason.lower():
                dr_suggestions['bad_specialty'].append(suggestion)
                category = "BAD_SPECIALTY"
            else:
                dr_suggestions['other_failed'].append(suggestion)
                category = "OTHER_FAILED"

        except Exception as e:
            suggestion = {
                'provider': provider_name,
                'address': address,
                'dateOfService': date_of_service,
                'reason': f"Error: {str(e)}"
            }
            dr_suggestions['other_failed'].append(suggestion)

    def logout(self):
        """Attempt to logout and ensure clean session"""
        try:
            logout_selectors = [
                'img[src*="Log_Out"]',
                'a:contains("Log out")',
                'button:contains("Log out")',
                'a[href*="logout"]'
            ]

            for selector in logout_selectors:
                try:
                    if self.wait_for_element_visible_improved(selector, timeout=2):
                        self.click(selector)
                        self.sleep(1.5)  # Reduced from 3

                        if "/account/login" in self.get_current_url() or "/logout" in self.get_current_url():
                            # Clear cookies and session storage for clean state
                            try:
                                self.execute_script("window.sessionStorage.clear();")
                                self.delete_all_cookies()
                            except:
                                pass
                            return True
                except:
                    continue

            self.open("https://www.medicare.gov/account/logout")
            self.sleep(1.5)  # Reduced from 3
            
            # Clear cookies and session storage
            try:
                self.execute_script("window.sessionStorage.clear();")
                self.delete_all_cookies()
            except:
                pass
            
            return "/account/login" in self.get_current_url() or "/logout" in self.get_current_url()

        except Exception as e:
            print(f"[Thread-{self.thread_id}] Logout error: {e}")
            # Still try to clear session even if logout fails
            try:
                self.execute_script("window.sessionStorage.clear();")
                self.delete_all_cookies()
            except:
                pass
            return False

    def write_result(self, username, good_providers, cn_providers, dr_suggestions, error_msg, session_info, input_data):
        """Thread-safe write to output file with fixed column order"""
        try:
            good_providers = good_providers or []
            cn_providers = cn_providers or []

            if not dr_suggestions or not isinstance(dr_suggestions, dict):
                dr_suggestions = {'bad_specialty': [], 'not_found': [], 'not_enrolled': [], 'other_failed': []}
            else:
                for key in ['bad_specialty', 'not_found', 'not_enrolled', 'other_failed']:
                    if key not in dr_suggestions or dr_suggestions[key] is None:
                        dr_suggestions[key] = []

            # Build row data with explicit column ordering
            row_data = {}
            
            # Session info columns first
            row_data['SESSION_FINGERPRINT'] = session_info.get('fingerprint', '')
            row_data['SESSION_TIMESTAMP'] = session_info.get('timestamp', '')
            row_data['BROWSER_TYPE'] = session_info.get('browser', '')
            row_data['THREAD_ID'] = session_info.get('thread_id', '')
            row_data['USER_AGENT'] = session_info.get('userAgent', '')[:100] if session_info.get('userAgent') else ''
            row_data['SCREEN_RESOLUTION'] = f"{session_info.get('screenWidth', '')}x{session_info.get('screenHeight', '')}"
            row_data['TIMEZONE'] = session_info.get('timezone', '')
            row_data['SESSION_DURATION'] = round(session_info.get('session_duration', 0), 2)
            row_data['DR_COUNT'] = len(good_providers) + len(cn_providers) if not error_msg else 0
            row_data['DR_COUNT_REGULAR'] = len(good_providers) if not error_msg else 0
            row_data['DR_COUNT_CN'] = len(cn_providers) if not error_msg else 0

            # Add input data columns
            for key, value in input_data.items():
                row_data[key] = value

            # Add DR1-DR20 columns (ALWAYS in order)
            if error_msg:
                row_data['DR1'] = error_msg
                for i in range(2, 21):
                    row_data[f'DR{i}'] = ''
            else:
                all_providers = good_providers + cn_providers

                for i in range(1, 21):
                    if i <= len(all_providers):
                        provider = all_providers[i-1]
                        acceptance_reason = provider.get('acceptanceReason', '')
                        is_cn_eligible = provider.get('isCnEligible', False)

                        if 'Good taxonomy' in acceptance_reason:
                            cn_eligible = "YES"
                        elif is_cn_eligible or 'Good for CN' in acceptance_reason:
                            cn_eligible = "YES"
                        else:
                            cn_eligible = "NO"

                        formatted_provider = f"{provider.get('provider', '')} // {provider.get('address', '')} // {provider.get('npi', '')} // {provider.get('enrollment', '')} // {provider.get('specialty', '')} // {provider.get('dateOfService', '')} // CN Eligible: {cn_eligible}"
                        row_data[f'DR{i}'] = formatted_provider
                    else:
                        row_data[f'DR{i}'] = ''

            # Add suggestion columns AFTER all DR columns
            def format_suggestions(suggestions_list):
                if not suggestions_list:
                    return ""
                formatted = []
                for suggestion in suggestions_list:
                    if suggestion:
                        provider_name = suggestion.get('provider', '') if isinstance(suggestion, dict) else ''
                        address = suggestion.get('address', '') if isinstance(suggestion, dict) else ''
                        date_service = suggestion.get('dateOfService', '') if isinstance(suggestion, dict) else ''
                        reason = suggestion.get('reason', '') if isinstance(suggestion, dict) else ''
                        formatted.append(f"{provider_name} // {address} // {date_service} // {reason}")
                return ' | '.join(formatted)

            row_data['DR_SUGGESTION_NOT_FOUND'] = format_suggestions(dr_suggestions.get('not_found', []))
            row_data['DR_SUGGESTION_NOT_ENROLLED'] = format_suggestions(dr_suggestions.get('not_enrolled', []))
            row_data['DR_SUGGESTION_OTHER'] = format_suggestions(dr_suggestions.get('other_failed', []))
            row_data['DR_SUGGESTION_BAD_SPECIALTY'] = format_suggestions(dr_suggestions.get('bad_specialty', []))

            # Define exact column order
            ordered_headers = [
                'SESSION_FINGERPRINT', 'SESSION_TIMESTAMP', 'BROWSER_TYPE', 'THREAD_ID',
                'USER_AGENT', 'SCREEN_RESOLUTION', 'TIMEZONE', 'SESSION_DURATION',
                'DR_COUNT', 'DR_COUNT_REGULAR', 'DR_COUNT_CN'
            ]
            
            # Add input data columns (preserve original order)
            for key in input_data.keys():
                if key not in ordered_headers:
                    ordered_headers.append(key)
            
            # Add DR1-DR20
            for i in range(1, 21):
                ordered_headers.append(f'DR{i}')
            
            # Add suggestion columns in specific order
            ordered_headers.extend([
                'DR_SUGGESTION_NOT_FOUND',
                'DR_SUGGESTION_NOT_ENROLLED',
                'DR_SUGGESTION_OTHER',
                'DR_SUGGESTION_BAD_SPECIALTY'
            ])

            # Thread-safe file writing with retry
            write_success = False
            for write_attempt in range(3):  # Try up to 3 times
                try:
                    with self.file_lock:
                        file_exists = os.path.exists(self.output_file)

                        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=ordered_headers, extrasaction='ignore')
                            
                            if not file_exists:
                                writer.writeheader()
                            
                            writer.writerow(row_data)
                        
                        write_success = True
                        break
                except Exception as write_error:
                    if write_attempt < 2:
                        time.sleep(0.5)
                    else:
                        print(f"[Thread-{self.thread_id}] CRITICAL: Failed to save {username} after 3 attempts: {write_error}")

        except Exception as e:
            print(f"[Thread-{self.thread_id}] ERROR preparing results: {e}")

    # 5. Simplified retry logic without recursion:
    def process_account_with_retry(self, username, password, input_data):
        """Process account with simple retry logic - NO RECURSION"""
        self.reset_depth()
        
        for attempt in range(MAX_RETRYABLE_ERRORS + 1):
            try:
                if attempt > 0:
                    # Simple page reset
                    try:
                        self.open("https://www.medicare.gov/account/login")
                        time.sleep(random.uniform(2, 3))  # Reduced
                    except Exception as e:
                        continue
                
                # Process the account
                success, error_type, should_retry = self.process_account(username, password, input_data)
                
                if success:
                    self.reset_depth()
                    return True
                
                # If not retryable or last attempt, give up
                if not should_retry or attempt >= MAX_RETRYABLE_ERRORS:
                    return False
                
                # Wait before retry
                time.sleep(random.uniform(2, 4))  # Reduced from 3-6
                
            except RecursionError as e:
                self.reset_depth()
                return False
                
            except Exception as e:
                if attempt >= MAX_RETRYABLE_ERRORS:
                    return False
                time.sleep(random.uniform(1, 2))  # Reduced
        
        return False
# 7. Add emergency reset method:
    def emergency_reset(self):
        """Emergency reset when things go wrong"""
        print(f"[Thread-{self.thread_id}] EMERGENCY RESET")
        
        # Reset all counters
        self.recursion_depth = 0
        self.refresh_count = 0
        self.processing_lead = False
        
        # Try to recover browser
        try:
            self.delete_all_cookies()
            self.execute_script("window.sessionStorage.clear();")
            self.open("https://www.medicare.gov/account/login")
            time.sleep(2)  # Reduced from 5
            return True
        except Exception as e:
            print(f"[Thread-{self.thread_id}] Emergency reset failed: {e}")
            return False

    def process_account(self, username, password, input_data):
        """Process single account - returns (success, error_type, should_retry)"""
        self.processing_lead = True

        try:
            print(f"[Thread-{self.thread_id}] Processing: {username}")

            session_info = self.collect_session_info("account_start")
            success, error_type, error_msg = self.attempt_login(username, password)

            if not success:

                if error_type == "2FA_DETECTED":
                    final_session = self.collect_session_info("2fa_detected")
                    self.write_result(username, [], [], {}, "Error: 2FA", final_session, input_data)
                    return False, error_type, False

                # Clean error message
                err_text = (error_msg or "").strip()
                try:
                    err_text = re.sub(r'^\s*alert:\s*', '', err_text, flags=re.IGNORECASE).strip()
                except:
                    pass

                final_session = self.collect_session_info("login_failed")
                self.write_result(username, [], [], {}, f"LOGIN_FAILED:{error_type} - {err_text}", final_session, input_data)
                
                # Check if error is retryable
                should_retry = self.is_retryable_error(error_type)
                return False, error_type, should_retry

            nav_success = self.navigate_to_claims()
            if not nav_success:
                final_session = self.collect_session_info("navigation_failed")
                self.write_result(username, [], [], {}, "NAVIGATION_FAILED", final_session, input_data)
                return False, "NAVIGATION_FAILED", True  # Retryable

            if self.is_captcha_present(timeout=5):
                if not self.solve_captcha():
                    final_session = self.collect_session_info("captcha_failed")
                    self.write_result(username, [], [], {}, "CAPTCHA_FAILED", final_session, input_data)
                    return False, "CAPTCHA_FAILED", True  # Changed to True - CAPTCHA should be retried
                self.sleep(2)  # Reduced from 3

            patient_state = input_data.get('PT State', '').strip()
            all_claims = self.get_all_claim_cards_basic_info(patient_state)
            good_providers, cn_providers, dr_suggestions = self.process_claims_with_taxonomy_evaluation(all_claims, patient_state)

            if len(good_providers) + len(cn_providers) == 0:
                error_msg = "NO VALID Doctors-old/companies/bad"
                final_session = self.collect_session_info("no_valid_doctors")
                self.write_result(username, [], [], dr_suggestions, error_msg, final_session, input_data)
            else:
                final_session = self.collect_session_info("processing_complete")
                self.write_result(username, good_providers, cn_providers, dr_suggestions, "", final_session, input_data)

            success_counter.increment()
            return True, "", False

        except Exception as e:
            print(f"[Thread-{self.thread_id}] Critical error: {e}")
            failure_counter.increment()
            return False, "EXCEPTION", True  # Retryable

        finally:
            self.processing_lead = False
            try:
                self.logout()
            except:
                pass


# FIXED: Worker thread that NEVER loses leads
def worker_thread(browser_type, thread_id, batch):
    """Worker thread with crash protection - ENSURES ALL LEADS ARE PROCESSED"""
    print(f"[Thread-{thread_id}] Starting with {len(batch)} leads")

    processor = None
    consecutive_failures = 0
    max_consecutive_failures = 5
    processed_leads = 0

    try:
        time.sleep(thread_id * 1)  # Reduced from 2
        processor = ThreadedMedicareProcessor(browser_type=browser_type, thread_id=thread_id)
        processor.setUp()
        time.sleep(1)  # Reduced from 2

        for idx, (username, password, input_data) in enumerate(batch):
            try:
                print(f"[Thread-{thread_id}] [{idx+1}/{len(batch)}] {username}")
                
                # ALWAYS count this lead as processed
                processed_counter.increment()
                processed_leads += 1
                
                success = processor.process_account_with_retry(username, password, input_data)
                
                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    
                # Emergency reset if too many failures, BUT CONTINUE PROCESSING
                if consecutive_failures >= max_consecutive_failures:
                    print(f"[Thread-{thread_id}] Emergency reset after {consecutive_failures} failures")
                    try:
                        processor.emergency_reset()
                        consecutive_failures = 0
                    except:
                        # Even if reset fails, continue with next lead
                        print(f"[Thread-{thread_id}] Reset failed, continuing anyway")
                        consecutive_failures = 0
                
            except RecursionError as e:
                print(f"[Thread-{thread_id}] RecursionError - skipping to next lead")
                failure_counter.increment()
                consecutive_failures = 0
                try:
                    processor.emergency_reset()
                except:
                    pass
                # CONTINUE to next lead instead of breaking
                    
            except Exception as e:
                print(f"[Thread-{thread_id}] Error: {str(e)[:100]} - continuing")
                failure_counter.increment()
                # CONTINUE to next lead instead of breaking

            time.sleep(random.uniform(1, 2))  # Reduced from 3-6

    except Exception as e:
        print(f"[Thread-{thread_id}] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if processor:
            try:
                processor.tearDown()
            except:
                pass
        print(f"[Thread-{thread_id}] FINISHED - Processed {processed_leads}/{len(batch)} leads")

def load_credentials(credentials_file):
    """Load credentials from CSV file"""
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(f"Credentials file not found: {credentials_file}")

    credentials = []
    with open(credentials_file, 'r', newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('username', '').strip()
            password = row.get('password', '').strip()
            if username and password:
                credentials.append((username, password, row))

    return credentials


def split_list(lst, n):
    """Split list into n roughly equal parts"""
    k, m = divmod(len(lst), n)
    return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]


def wait_for_scheduled_start(delay_hours=0, delay_minutes=0):
    """Wait for scheduled start time with countdown display"""
    total_seconds = (delay_hours * 3600) + (delay_minutes * 60)
    
    if total_seconds <= 0:
        return  # Start immediately
    
    start_time = datetime.now()
    scheduled_time = start_time + timedelta(hours=delay_hours, minutes=delay_minutes)
    
    print("\n" + "="*100)
    print("⏰ SCHEDULED START")
    print("="*100)
    print(f"Current time:    {start_time.strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f"Scheduled start: {scheduled_time.strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f"Delay: {delay_hours} hours and {delay_minutes} minutes")
    print("="*100)
    print("\n💤 Waiting for scheduled time...")
    print("(Press Ctrl+C to cancel and exit)\n")
    
    try:
        while True:
            now = datetime.now()
            remaining = (scheduled_time - now).total_seconds()
            
            if remaining <= 0:
                break
            
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60)
            
            # Clear line and print countdown
            print(f"\r⏳ Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d}  ", end='', flush=True)
            
            time.sleep(1)
        
        print("\n\n✅ Scheduled time reached! Starting processing...\n")
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n\n❌ Scheduled start cancelled by user. Exiting...")
        sys.exit(0)


def test_run_threaded_batch_processing():
    """Main threaded batch processing function"""
    print("="*100)
    print("MEDICARE CLAIMS PROCESSOR - FAST & RELIABLE")
    print("="*100)
    print(f"Input file: {CREDENTIALS_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Threads: {NUM_THREADS}")
    print(f"Browser distribution: {BROWSER_DISTRIBUTION}")
    print(f"Retry: Up to {MAX_RETRYABLE_ERRORS} retries for errors")
    print("="*100)

    # Wait for scheduled start time if configured
    wait_for_scheduled_start(DELAY_START_HOURS, DELAY_START_MINUTES)

    try:
        credentials = load_credentials(CREDENTIALS_FILE)
        total_accounts = len(credentials)
        print(f"Found {total_accounts} accounts to process")

        batches = split_list(credentials, NUM_THREADS)

        # Start worker threads
        threads = []
        thread_id = 0
        batch_idx = 0

        for browser, count in BROWSER_DISTRIBUTION.items():
            for i in range(count):
                if batch_idx < len(batches):
                    batch = batches[batch_idx]
                    t = threading.Thread(
                        target=worker_thread,
                        args=(browser, thread_id, batch),
                        daemon=False
                    )
                    t.start()
                    threads.append(t)
                    thread_id += 1
                    batch_idx += 1
                    time.sleep(1)

        print(f"\nStarted {len(threads)} worker threads")
        print("="*100 + "\n")

        # Wait for threads to finish
        for t in threads:
            t.join()

        print(f"\n{'='*100}")
        print("PROCESSING COMPLETE")
        print(f"{'='*100}")
        print(f"Total leads: {total_accounts}")
        print(f"Processed: {processed_counter.get()}")
        print(f"Successful: {success_counter.get()}")
        print(f"Failed: {failure_counter.get()}")
        if total_accounts > 0:
            print(f"Success rate: {(success_counter.get()/total_accounts)*100:.1f}%")
        if processed_counter.get() != total_accounts:
            print(f"⚠ WARNING: Missing {total_accounts - processed_counter.get()} leads!")
        print(f"\nResults saved to: {OUTPUT_FILE}")
        print(f"{'='*100}")

    except Exception as e:
        print(f"Batch processing error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_run_threaded_batch_processing()