"""
TEST SCRIPT: Detailed Claims Extractor
========================================
This script extracts COMPLETE claim details (all services, amounts, etc.)
for a single account and saves everything as JSON in CSV cells.

USAGE:
1. Edit the config below (username, password, max claims)
2. Run: python test_detailed_claims_extractor.py
3. Check output: detailed_claims_test_output.csv
"""

import csv
import os
import random
import time
import json
from datetime import datetime, date, timedelta
from seleniumbase import SB
import calendar
import re
from DR_eval import NPIRegistryService, PECOSEnrollmentService, TaxonomyBasedSpecialtyValidator
from improved_captcha_handler import ImprovedCaptchaHandler

# ===================== TEST CONFIG ===================== #
TEST_USERNAME = "FRANCINEMELENDEZ2525"           # ← CHANGE THIS
TEST_PASSWORD = "larry@48824565@!"                    # ← CHANGE THIS
MAX_CLAIMS_TO_EXTRACT = 1                        # ← How many claims to extract (from latest)
PATIENT_STATE = "NY"                             # ← Patient state for validation
OUTPUT_FILE = "detailed_claims_test_output.csv"
SKIP_VALIDATION = True                           # ← Set to True to extract ALL claims (skip doctor validation)

# Timeouts
LOGIN_TIMEOUT = 25
CLAIMS_LOAD_TIMEOUT = 20
DETAIL_TIMEOUT = 10
# ======================================================= #


class DetailedClaimsExtractor:
    """Extract complete claim details with all services and financial data"""
    
    def __init__(self, sb):
        """Initialize with SB context (same pattern as main processor uses driver)"""
        self.sb = sb
        self.npi_service = NPIRegistryService()
        self.pecos_service = PECOSEnrollmentService()
        self.specialty_validator = TaxonomyBasedSpecialtyValidator()
        
        # Create a mock object for captcha handler that looks like BaseCase
        class MockBaseCase:
            def __init__(self, sb):
                self.driver = sb.driver
                self.execute_script = sb.execute_script
                self.find_elements = sb.find_elements
                self.find_element = sb.find_element
                self.sleep = sb.sleep
                self.is_element_present = sb.is_element_present
                self.is_element_visible = sb.is_element_visible
                self.wait_for_element_present = sb.wait_for_element_present
                self.wait_for_element_visible = sb.wait_for_element_visible
                self.is_text_visible = sb.is_text_visible
                self.get_page_source = sb.get_page_source
                self.switch_to_frame = sb.switch_to_frame
                self.switch_to_default_content = sb.switch_to_default_content
                self.click = sb.click
        
        mock = MockBaseCase(sb)
        self.captcha_handler = ImprovedCaptchaHandler(mock)
    
    def wait_for_element_visible_improved(self, selector, timeout=10):
        """Wait for element visibility (same as main processor)"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                elements = self.sb.find_elements(selector)
                for element in elements:
                    if element.is_displayed():
                        return True
            except:
                pass
            self.sb.sleep(0.3)
        return False
    
    def wait_for_login_completion(self, timeout=25):
        """Wait for login to complete and dashboard to load"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check for CAPTCHA during wait
                if self.captcha_handler.is_captcha_present(timeout=1):
                    print("  ⚠️  CAPTCHA appeared during login! Solving...")
                    if not self.captcha_handler.solve_captcha():
                        return False
                    self.sb.sleep(3)
                
                # Check for error alerts
                error_elements = self.sb.find_elements(".ds-c-alert--error")
                for element in error_elements:
                    if element.is_displayed():
                        error_text = element.text.strip()
                        print(f"    ❌ Login error: {error_text[:100]}")
                        return False
                
                # Check for success indicators
                success_selectors = [
                    'a[href="/my/claims"]',
                    'a[aria-label*="Check my claims"]',
                    'button[aria-label*="Show my claims"]',
                    '.m-c-card'
                ]
                
                for selector in success_selectors:
                    if self.wait_for_element_visible_improved(selector, timeout=1):
                        return True
                
                # Check if we're on dashboard by URL
                current_url = self.sb.get_current_url()
                if "/my/" in current_url and "/login" not in current_url:
                    return True
                
            except Exception as e:
                print(f"    Warning during login wait: {e}")
            
            self.sb.sleep(0.5)
        
        # Timeout - check if we're at least off login page
        current_url = self.sb.get_current_url()
        if "/login" in current_url:
            print("    ❌ Still on login page after timeout")
            return False
        else:
            print("    ⚠️  Timeout but not on login page - assuming success")
            return True
    
    def attempt_login(self, username, password):
        """Login to Medicare.gov - TWO-STEP PROCESS"""
        print(f"\n🔐 Logging in as: {username}")
        
        try:
            # Clear session
            print("  → Clearing cookies and session...")
            try:
                self.sb.delete_all_cookies()
                self.sb.execute_script("window.sessionStorage.clear(); window.localStorage.clear();")
            except Exception as e:
                print(f"    Warning: {e}")
            
            # STEP 1: Open login page and wait for it to fully load
            print("\n📝 STEP 1: Username Entry")
            print("  → Opening login page...")
            try:
                self.sb.driver.get("https://www.medicare.gov/account/login")
            except Exception as e:
                print(f"    ⚠️  Page load interrupted: {e}")
            
            print("  → Waiting for page to fully load...")
            self.sb.sleep(5)
            
            # Verify page loaded
            try:
                current_url = self.sb.get_current_url()
                page_title = self.sb.get_title()
                print(f"    URL: {current_url}")
                print(f"    Title: {page_title}")
            except:
                pass
            
            # STEP 2: Wait for username field
            print("  → Looking for username field...")
            if not self.wait_for_element_visible_improved('input[name="username"]', timeout=20):
                return False, "PAGE_LOAD_FAILED - Username field not found"
            print("    ✓ Username field found")
            
            # STEP 3: Enter username (character by character for human-like behavior)
            print("  → Entering username...")
            username_selector = 'input[name="username"]'
            try:
                username_field = self.sb.find_element(username_selector)
                username_field.clear()
                for char in username:
                    username_field.send_keys(char)
                    self.sb.sleep(random.uniform(0.01, 0.02))
                self.sb.sleep(0.3)
                print("    ✓ Username entered")
            except Exception as e:
                return False, f"USERNAME_INPUT_FAILED: {str(e)}"
            
            # STEP 4: Click Continue button
            print("  → Clicking 'Continue' button...")
            continue_selectors = [
                'button[type="submit"]',
                'button.ds-c-button--solid',
                '//button[contains(text(), "Continue")]'
            ]
            
            continue_clicked = False
            for selector in continue_selectors:
                try:
                    if self.sb.is_element_present(selector):
                        self.sb.click(selector)
                        print("    ✓ Continue clicked")
                        continue_clicked = True
                        break
                except:
                    continue
            
            if not continue_clicked:
                return False, "NAVIGATION_FAILED - Could not click Continue button"
            
            self.sb.sleep(2)
            
            # STEP 5: Check for CAPTCHA on password page
            print("\n🔍 Checking for CAPTCHA...")
            if self.captcha_handler.is_captcha_present(timeout=3):
                print("  ⚠️  CAPTCHA detected! Solving...")
                if not self.captcha_handler.solve_captcha():
                    return False, "CAPTCHA_FAILED - Failed to solve CAPTCHA on password page"
                print("  ✓ CAPTCHA solved")
            else:
                print("  ✓ No CAPTCHA detected")
            
            # STEP 6: Wait for password field
            print("\n🔒 STEP 2: Password Entry")
            print("  → Looking for password field...")
            if not self.wait_for_element_visible_improved('input[name="password"]', timeout=15):
                return False, "PASSWORD_PAGE_FAILED - Password field not found"
            print("    ✓ Password field found")
            
            # STEP 7: Enter password (character by character)
            print("  → Entering password...")
            password_selector = 'input[name="password"]'
            try:
                password_field = self.sb.find_element(password_selector)
                password_field.clear()
                for char in password:
                    password_field.send_keys(char)
                    self.sb.sleep(random.uniform(0.01, 0.02))
                self.sb.sleep(0.3)
                print("    ✓ Password entered")
            except Exception as e:
                return False, f"PASSWORD_INPUT_FAILED: {str(e)}"
            
            # STEP 8: Click Log in button
            print("  → Clicking 'Log in' button...")
            login_selectors = [
                'button#login-button',
                'button[type="submit"]',
                '//button[contains(text(), "Log in")]'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    if self.sb.is_element_present(selector):
                        self.sb.click(selector)
                        print("    ✓ Log in clicked")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                return False, "LOGIN_BUTTON_FAILED - Could not click Log in button"
            
            self.sb.sleep(1)
            
            # STEP 9: Check for post-login CAPTCHA
            print("\n🔍 Checking for post-login CAPTCHA...")
            if self.captcha_handler.is_captcha_present(timeout=2):
                print("  ⚠️  Post-login CAPTCHA detected! Solving...")
                if not self.captcha_handler.solve_captcha():
                    return False, "CAPTCHA_FAILED - Failed to solve CAPTCHA after login button click"
                print("  ✓ Post-login CAPTCHA solved")
            else:
                print("  ✓ No post-login CAPTCHA")
            
            # STEP 10: Wait for login to complete
            print("\n⏳ Waiting for dashboard to load...")
            if not self.wait_for_login_completion():
                return False, "LOGIN_TIMEOUT - Dashboard not reached"
            
            print("✅ LOGIN SUCCESSFUL\n")
            return True, None
            
        except Exception as e:
            print(f"❌ Login exception: {e}")
            return False, str(e)
    
    def navigate_to_claims(self):
        """Navigate to claims page"""
        print("📄 Navigating to claims page...")
        
        try:
            self.sb.open("https://www.medicare.gov/my/claims")
            self.sb.sleep(2)
            
            # Wait for claims to load
            if self.wait_for_element_visible_improved('.m-c-card', timeout=CLAIMS_LOAD_TIMEOUT):
                cards = self.sb.find_elements('.m-c-card')
                print(f"✅ Claims page loaded - Found {len(cards)} initial claims\n")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False
    
    def is_company(self, name):
        """Check if provider name is a company"""
        if not name:
            return True
        u = name.upper()
        company_keywords = [
            " LLC", " INC", " LLP", " LTD", " PLLC", " CORP",
            " CENTER", " CLINIC", " GROUP", " HOSPITAL", " ASSOCIATES"
        ]
        return any(k in u for k in company_keywords)
    
    def validate_doctor(self, provider_name, state):
        """Quick validation using NPI + PECOS"""
        try:
            providers = self.npi_service.search_providers(provider_name, state, max_results=1)
            
            if not providers:
                return False, "Not found in NPI"
            
            provider = providers[0]
            validation_result = self.npi_service.validate_provider_basic_criteria(provider)
            
            if not validation_result['isValid']:
                return False, "Basic validation failed"
            
            taxonomy_evaluation = self.specialty_validator.evaluate_provider_by_taxonomy(provider)
            
            if taxonomy_evaluation['category'] in ['GOOD', 'CN_ELIGIBLE']:
                return True, "Valid"
            
            # Check if bad but CN eligible
            if taxonomy_evaluation['category'] == 'BAD' and taxonomy_evaluation.get('is_cn_eligible'):
                return True, "Valid (CN)"
            
            return False, f"Bad specialty: {taxonomy_evaluation.get('taxonomy_code', 'Unknown')}"
            
        except Exception as e:
            return False, str(e)
    
    def extract_complete_claim_details(self):
        """Extract ALL claim details as JSON-ready dict - MATCHES EXACT HTML STRUCTURE"""
        try:
            print("    [1/4] Waiting for claim details page to fully load...")
            
            # Wait for the main content section to load
            if not self.wait_for_element_visible_improved('.ds-l-container', timeout=15):
                print("      ❌ Claim detail page didn't load")
                return None
            
            # Extra wait for dynamic content
            self.sb.sleep(5)
            print("      ✓ Page loaded")
            
            claim_data = {
                'basic_info': {},
                'services': [],
                'summary': {}
            }
            
            # === BASIC INFO ===
            print("    [2/4] Extracting basic info...")
            print("      ⏳ Waiting extra time for content to render...")
            self.sb.sleep(8)  # Even longer wait
            
            # Scroll to ensure content loads
            self.sb.execute_script("window.scrollTo(0, 0);")
            self.sb.sleep(2)
            
            # Use JavaScript to extract all the data directly from DOM
            print("      → Using JavaScript extraction method...")
            try:
                js_extraction = self.sb.execute_script("""
                    const data = {};
                    
                    // Find all label-value pairs in the basic info section
                    const labels = Array.from(document.querySelectorAll('.ds-text-body--md'));
                    
                    labels.forEach(label => {
                        const text = label.textContent.trim();
                        const parent = label.parentElement;
                        
                        if (parent) {
                            const headings = parent.querySelectorAll('.ds-text-heading--lg, .ds-text-heading--md');
                            if (headings.length > 0) {
                                const value = headings[0].textContent.trim();
                                data[text] = value;
                            }
                        }
                    });
                    
                    return data;
                """)
                
                print(f"      ✓ JS extracted {len(js_extraction)} fields")
                for key, value in js_extraction.items():
                    print(f"        • {key}: {value[:50]}")
                
                # Map extracted data to our field names
                field_mapping = {
                    'Date of service': 'date_of_service',
                    'Provider': 'provider',
                    'Provider address': 'provider_address',
                    'Claim processed on': 'claim_processed_on',
                    'Practicing providers': 'practicing_providers'
                }
                
                for js_key, field_name in field_mapping.items():
                    if js_key in js_extraction:
                        claim_data['basic_info'][field_name] = js_extraction[js_key]
                        print(f"      ✓ Mapped {field_name}")
                    else:
                        claim_data['basic_info'][field_name] = ''
                        print(f"      ⚠️  {js_key} not in JS extraction")
                
            except Exception as e:
                print(f"      ❌ JavaScript extraction failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback: Set empty values
                for field in ['date_of_service', 'provider', 'provider_address', 'claim_processed_on', 'practicing_providers']:
                    claim_data['basic_info'][field] = ''
            
            # Get claim number - try from the JS extraction first, then from other sources
            try:
                if 'Claim number' in js_extraction:
                    claim_data['basic_info']['claim_number'] = js_extraction['Claim number']
                    print(f"      ✓ Claim number from JS: {claim_data['basic_info']['claim_number']}")
                else:
                    # Try to extract from h3 with "Claim number"
                    try:
                        claim_h3 = self.sb.find_element("xpath=//h3[contains(text(), 'Claim number')]", timeout=2)
                        parent = claim_h3.find_element("xpath", "..")
                        claim_value = parent.find_element("xpath", "./div[contains(@class, 'ds-text-heading')]")
                        claim_data['basic_info']['claim_number'] = claim_value.text.strip()
                        print(f"      ✓ Claim number from XPath: {claim_data['basic_info']['claim_number']}")
                    except:
                        claim_data['basic_info']['claim_number'] = ''
                        print(f"      ⚠️  Claim number not found")
            except Exception as e:
                print(f"      ⚠️  Claim number extraction error: {e}")
                claim_data['basic_info']['claim_number'] = ''
            
            # === SERVICES ===
            print("    [3/4] Extracting services...")
            try:
                # Services are in ._container_uudit_1 within ._grid_uudit_5
                # Fix: Remove "css selector=" prefix - just use the class name
                service_containers = self.sb.find_elements("._container_uudit_1")
                print(f"      Found {len(service_containers)} service containers")
                
                for idx, container in enumerate(service_containers, 1):
                    service = {}
                    
                    # Get service name and procedure code from ._serviceName_uudit_19
                    try:
                        service_elem = container.find_element("css selector", "._serviceName_uudit_19 .ds-text-heading--md")
                        full_service = service_elem.text.strip()
                        
                        # Parse "SERVICE NAME (CODE)"
                        if '(' in full_service and ')' in full_service:
                            service['service_name'] = full_service[:full_service.rfind('(')].strip()
                            service['procedure_code'] = full_service[full_service.rfind('(')+1:full_service.rfind(')')].strip()
                        else:
                            service['service_name'] = full_service
                            service['procedure_code'] = ''
                    except Exception as e:
                        print(f"        ⚠️  Service name extraction error: {e}")
                        service['service_name'] = ''
                        service['procedure_code'] = ''
                    
                    # Get other service fields - label and value are SIBLINGS
                    service_fields = [
                        ('Qty', 'quantity'),
                        ('Provider charged', 'provider_charged'),
                        ('Medicare approved', 'medicare_approved'),
                        ('Applied to deductible', 'applied_to_deductible'),
                        ('Coinsurance', 'coinsurance'),
                        ('You may be billed', 'you_may_be_billed')
                    ]
                    
                    for display_name, field_name in service_fields:
                        try:
                            # Label and value are siblings, use following-sibling
                            value_div = container.find_element("xpath", f".//div[contains(@class, 'ds-text-body--md') and text()='{display_name}']/following-sibling::div[contains(@class, 'ds-text-heading--md')]")
                            service[field_name] = value_div.text.strip()
                        except:
                            service[field_name] = ''
                    
                    if service.get('service_name') or service.get('procedure_code'):
                        claim_data['services'].append(service)
                        svc_name = service.get('service_name', 'N/A')[:40]
                        svc_code = service.get('procedure_code', '')
                        print(f"      ✓ Service {idx}: {svc_name} ({svc_code})")
            except Exception as e:
                print(f"      ⚠️  Service extraction error: {e}")
            
            print(f"      ✓ Extracted {len(claim_data['services'])} services total")
            
            # === SUMMARY ===
            print("    [4/4] Extracting financial summary...")
            print("      → Using JavaScript extraction for summary...")
            
            try:
                js_summary = self.sb.execute_script("""
                    const summary = {};
                    
                    // Summary fields are in h3 tags
                    const h3Labels = Array.from(document.querySelectorAll('h3.ds-text-body--md'));
                    
                    h3Labels.forEach(h3 => {
                        const text = h3.textContent.trim();
                        const parent = h3.parentElement;
                        
                        if (parent) {
                            const headings = parent.querySelectorAll('.ds-text-heading--md');
                            if (headings.length > 0) {
                                const value = headings[0].textContent.trim();
                                summary[text] = value;
                            }
                        }
                    });
                    
                    return summary;
                """)
                
                print(f"      ✓ JS extracted {len(js_summary)} summary fields")
                
                # Map extracted data
                summary_mapping = {
                    'Total amount charged': 'total_amount_charged',
                    'Total Medicare approved': 'total_medicare_approved',
                    'Blood deductible': 'blood_deductible',
                    'Physical therapy charges': 'physical_therapy_charges',
                    'Psychiatric charges': 'psychiatric_charges',
                    'Occupational therapy charges': 'occupational_therapy_charges',
                    'Total patient paid the provider': 'total_patient_paid_provider',
                    'Total Medicare paid you': 'total_medicare_paid_you',
                    'Total Medicare paid the provider': 'total_medicare_paid_provider',
                    'Total applied to deductible': 'total_applied_to_deductible',
                    'Total coinsurance': 'total_coinsurance',
                    'Total you may be billed': 'total_you_may_be_billed'
                }
                
                for js_key, field_name in summary_mapping.items():
                    # Some h3 tags have extra content (tooltips), so use startswith
                    found = False
                    for extracted_key, extracted_value in js_summary.items():
                        if extracted_key.startswith(js_key):
                            claim_data['summary'][field_name] = extracted_value
                            found = True
                            break
                    
                    if not found:
                        claim_data['summary'][field_name] = ''
                
            except Exception as e:
                print(f"      ❌ JavaScript summary extraction failed: {e}")
                # Set all to empty
                for field in ['total_amount_charged', 'total_medicare_approved', 'blood_deductible', 
                             'physical_therapy_charges', 'psychiatric_charges', 'occupational_therapy_charges',
                             'total_patient_paid_provider', 'total_medicare_paid_you', 'total_medicare_paid_provider',
                             'total_applied_to_deductible', 'total_coinsurance', 'total_you_may_be_billed']:
                    claim_data['summary'][field] = ''
            
            # Show summary of what we got
            total_charged = claim_data['summary'].get('total_amount_charged', 'N/A')
            total_billed = claim_data['summary'].get('total_you_may_be_billed', 'N/A')
            print(f"      ✓ Summary: Charged={total_charged}, You owe={total_billed}")
            print("    ✅ Complete claim data extracted!")
            
            return claim_data
            
        except Exception as e:
            print(f"    ❌ Critical error extracting claim: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def click_claim_by_index(self, index):
        """Click claim card to open details"""
        try:
            print("  → Finding claim cards...")
            cards = self.sb.find_elements('.m-c-card')
            print(f"    Found {len(cards)} cards total")
            
            if index >= len(cards):
                print(f"    ❌ Index {index} out of range")
                return False
            
            card = cards[index]
            print(f"  → Scrolling to claim {index}...")
            
            # Scroll into view
            self.sb.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            self.sb.sleep(0.5)
            
            # Find and click detail button
            print("  → Finding detail button...")
            detail_button = card.find_element("xpath", ".//a[contains(@aria-label, 'Open claim details')]")
            
            current_url = self.sb.get_current_url()
            print("  → Clicking to open details...")
            detail_button.click()
            self.sb.sleep(2)
            
            # Wait for URL change
            print("  → Waiting for detail page to load...")
            start = time.time()
            while time.time() - start < DETAIL_TIMEOUT:
                new_url = self.sb.get_current_url()
                if new_url != current_url and "/claims/" in new_url:
                    print(f"    ✓ Detail page loaded: {new_url}")
                    self.sb.sleep(2)  # Extra wait for content
                    return True
                self.sb.sleep(0.5)
            
            print("    ❌ Timeout waiting for detail page")
            return False
            
        except Exception as e:
            print(f"  ❌ Error clicking claim: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_back_to_claims(self):
        """Go back to claims list"""
        try:
            # Try Back to claims link
            try:
                self.sb.click("xpath=//a[contains(text(), 'Back to claims')]")
                self.sb.sleep(2)
                return True
            except:
                pass
            
            # Try browser back
            self.sb.driver.back()
            self.sb.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Error navigating back: {e}")
            return False
    
    def wait_for_element_visible_improved(self, selector, timeout=10):
        """Wait for element visibility (same as main processor)"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                elements = self.sb.find_elements(selector)
                for element in elements:
                    if element.is_displayed():
                        return True
            except:
                pass
            self.sb.sleep(0.3)
        return False
    
    def run_extraction(self):
        """Main extraction function"""
        print("="*80)
        print("DETAILED CLAIMS EXTRACTOR - TEST MODE v2.0")
        print("="*80)
        print(f"Username: {TEST_USERNAME}")
        print(f"Max claims to extract: {MAX_CLAIMS_TO_EXTRACT}")
        print(f"Patient state: {PATIENT_STATE}")
        print(f"Validation: {'DISABLED' if SKIP_VALIDATION else 'ENABLED'}")
        print(f"Output file: {OUTPUT_FILE}")
        print("="*80 + "\n")
        
        # Login
        success, error = self.attempt_login(TEST_USERNAME, TEST_PASSWORD)
        if not success:
            print(f"❌ LOGIN FAILED: {error}")
            return
        
        # Navigate to claims
        if not self.navigate_to_claims():
            print("❌ Failed to navigate to claims")
            return
        
        # Wait for claims to fully load with content
        print("⏳ Waiting for claims to fully load with content...")
        self.sb.sleep(5)
        
        # Wait for cards to have actual content (not just skeleton loaders)
        max_wait = 15
        start_time = time.time()
        cards_with_content = []
        
        while time.time() - start_time < max_wait:
            cards = self.sb.find_elements('.m-c-card')
            
            if cards:
                # Check if cards have actual text content (not just loading skeletons)
                cards_with_text = 0
                for card in cards:
                    if card.text and len(card.text.strip()) > 10:
                        cards_with_text += 1
                
                if cards_with_text > 0:
                    print(f"✅ Found {len(cards)} claim cards with content loaded")
                    cards_with_content = cards
                    break
                else:
                    print(f"  ⏳ Found {len(cards)} cards but no content yet... (waiting)")
            else:
                print("  ⏳ No cards found yet... (waiting)")
            
            self.sb.sleep(2)
        
        if len(cards_with_content) == 0:
            print("❌ No claims loaded after waiting")
            print("💡 The page might still be loading. Try increasing CLAIMS_LOAD_TIMEOUT.")
            return
        
        cards = cards_with_content
        print(f"📋 Ready to process {len(cards)} claims\n")
        
        # Extract basic info from cards first
        if SKIP_VALIDATION:
            print(f"\n🔍 Scanning claims (VALIDATION DISABLED - extracting all)...")
        else:
            print(f"\n🔍 Scanning claims to find valid doctors...")
        
        valid_claims = []
        
        for i, card in enumerate(cards):
            if len(valid_claims) >= MAX_CLAIMS_TO_EXTRACT:
                print(f"\n✅ Reached maximum of {MAX_CLAIMS_TO_EXTRACT} claims")
                break
            
            try:
                card_text = card.text
                
                # Debug: Show card content
                if i < 3:  # Show first 3 cards for debugging
                    print(f"\n[DEBUG] Card {i+1} text preview: {card_text[:100]}...")
                
                # Extract provider name from card
                provider_match = re.search(r'([A-Z]+,\s*[A-Z\s\'-]+)', card_text)
                if not provider_match:
                    print(f"  [{i+1}] No provider name pattern found in card text")
                    # Try to extract anyway - just use first line as provider
                    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                    if len(lines) >= 2:
                        provider_name = lines[1]  # Usually second line after "Medical claim"
                    else:
                        print(f"  [{i+1}] Card has insufficient text, skipping")
                        continue
                else:
                    provider_name = provider_match.group(1).strip()
                
                # Extract date
                date_match = re.search(r'(\d{2}/\d{2}/\d{2,4})', card_text)
                service_date = date_match.group(1) if date_match else ''
                
                # Validation logic
                if SKIP_VALIDATION:
                    # Skip all validation - extract everything
                    print(f"  [{i+1}] {provider_name[:40]} - {service_date} → ✅ SELECTED (no validation)")
                    valid_claims.append({
                        'index': i,
                        'provider': provider_name,
                        'date': service_date
                    })
                else:
                    # Apply normal validation
                    # Skip companies
                    if self.is_company(provider_name):
                        print(f"  [{i+1}] {provider_name[:40]} → SKIP (company)")
                        continue
                    
                    # Validate doctor
                    print(f"  [{i+1}] {provider_name[:40]} - {service_date}", end=' ')
                    is_valid, reason = self.validate_doctor(provider_name, PATIENT_STATE)
                    
                    if is_valid:
                        print(f"→ ✅ VALID")
                        valid_claims.append({
                            'index': i,
                            'provider': provider_name,
                            'date': service_date
                        })
                    else:
                        print(f"→ ❌ {reason}")
                
            except Exception as e:
                continue
        
        if len(valid_claims) == 0:
            print("\n❌ No valid claims found")
            if not SKIP_VALIDATION:
                print("💡 TIP: Set SKIP_VALIDATION = True in config to extract all claims without filtering")
            else:
                print("💡 TIP: Try increasing MAX_CLAIMS_TO_EXTRACT or check account has claims")
            return
        
        print(f"\n✅ Found {len(valid_claims)} valid claims to extract")
        print("="*80)
        
        # Now extract detailed info for each valid claim
        detailed_results = []
        
        for idx, claim_info in enumerate(valid_claims):
            print(f"\n📥 Extracting claim {idx+1}/{len(valid_claims)}: {claim_info['provider'][:40]}")
            
            # Click to open details
            if not self.click_claim_by_index(claim_info['index']):
                print("  ❌ Failed to open claim details")
                continue
            
            # Extract complete details
            print("  → Extracting all data...")
            claim_details = self.extract_complete_claim_details()
            
            if claim_details:
                claim_details['validation_info'] = {
                    'provider_from_card': claim_info['provider'],
                    'date_from_card': claim_info['date']
                }
                detailed_results.append(claim_details)
                
                # Show summary
                service_count = len(claim_details.get('services', []))
                total_charged = claim_details.get('summary', {}).get('total_amount_charged', 'N/A')
                total_billed = claim_details.get('summary', {}).get('total_you_may_be_billed', 'N/A')
                print(f"  ✅ Extracted: {service_count} services")
                print(f"     Charged: {total_charged}, Patient owes: {total_billed}")
            else:
                print("  ❌ Failed to extract details")
            
            # Go back to claims list
            self.navigate_back_to_claims()
            self.sb.sleep(1)
        
        # Save results
        self.save_detailed_results(detailed_results)
        
        print("\n" + "="*80)
        print("✅ EXTRACTION COMPLETE")
        print("="*80)
        print(f"Total claims extracted: {len(detailed_results)}")
        print(f"Output saved to: {OUTPUT_FILE}")
        print("="*80)
    
    def save_detailed_results(self, results):
        """Save results to CSV with JSON in cells"""
        print(f"\n💾 Saving {len(results)} claims to CSV...")
        
        try:
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                headers = [
                    'claim_number',
                    'provider',
                    'provider_address',
                    'date_of_service',
                    'claim_processed_on',
                    'service_count',
                    'total_amount_charged',
                    'total_medicare_approved',
                    'total_you_may_be_billed',
                    'complete_claim_json'  # Full claim data as JSON
                ]
                
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for claim in results:
                    basic = claim.get('basic_info', {})
                    summary = claim.get('summary', {})
                    services = claim.get('services', [])
                    
                    row = {
                        'claim_number': basic.get('claim_number', ''),
                        'provider': basic.get('provider', ''),
                        'provider_address': basic.get('provider_address', ''),
                        'date_of_service': basic.get('date_of_service', ''),
                        'claim_processed_on': basic.get('claim_processed_on', ''),
                        'service_count': len(services),
                        'total_amount_charged': summary.get('total_amount_charged', ''),
                        'total_medicare_approved': summary.get('total_medicare_approved', ''),
                        'total_you_may_be_billed': summary.get('total_you_may_be_billed', ''),
                        'complete_claim_json': json.dumps(claim, ensure_ascii=False, indent=2)  # Full JSON with formatting
                    }
                    
                    writer.writerow(row)
            
            print(f"✅ Saved to: {OUTPUT_FILE}")
            
            # Print JSON preview
            if len(results) > 0:
                print(f"\n📋 Preview of first claim JSON:")
                print("─" * 80)
                preview = json.dumps(results[0], indent=2, ensure_ascii=False)
                # Show first 800 characters
                if len(preview) > 800:
                    print(preview[:800] + "\n... (truncated)")
                else:
                    print(preview)
                print("─" * 80)
            
        except Exception as e:
            print(f"❌ Save error: {e}")


def run_test():
    """Run the test extraction - USES SB() CONTEXT MANAGER"""
    
    # Validate config
    if TEST_USERNAME == "your_username@example.com":
        print("="*80)
        print("❌ ERROR: Please configure TEST_USERNAME and TEST_PASSWORD")
        print("="*80)
        print("\nEdit the top of this file:")
        print('  TEST_USERNAME = "your_actual_username@example.com"')
        print('  TEST_PASSWORD = "your_actual_password"')
        print('  MAX_CLAIMS_TO_EXTRACT = 5  # or however many you want')
        print('  PATIENT_STATE = "NY"  # Your state')
        print("\nThen run again.")
        print("="*80)
        return
    
    print("🌐 Starting browser...")
    print("   (This may take 10-15 seconds...)")
    
    # Use SB() context manager with timeout settings
    with SB(uc=True, headed=True, browser='chrome', page_load_strategy='normal') as sb:
        # Set page load timeout
        try:
            sb.driver.set_page_load_timeout(30)
            print("✓ Browser started (timeout: 30s)")
        except Exception as e:
            print(f"   Warning: Could not set timeout: {e}")
        
        # Anti-bot measures
        try:
            sb.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            print("✓ Anti-bot measures applied")
        except Exception as e:
            print(f"   Warning: Anti-bot error: {e}")
        
        time.sleep(1)
        
        # Create extractor and run
        print("✓ Initializing extractor...\n")
        extractor = DetailedClaimsExtractor(sb)
        extractor.run_extraction()
    
    print("\n🚪 Browser closed")


if __name__ == "__main__":
    run_test()
