"""
IMPROVED CAPTCHA HANDLING FOR MEDICARE CLAIMS PROCESSOR

This module provides robust CAPTCHA handling with:
1. Continuous monitoring for CAPTCHA re-appearance
2. Patient waiting for Proceed button loading
3. Multiple verification attempts
4. Periodic re-checking after resolution
"""

import time
from datetime import datetime

class ImprovedCaptchaHandler:
    """Enhanced CAPTCHA handler with persistent monitoring"""

    def __init__(self, browser_instance):
        self.browser = browser_instance
        self.max_solve_attempts = 5
        self.proceed_timeout = 45  # Wait up to 45 seconds for proceed to complete
        self.verification_checks = 3  # Verify CAPTCHA is gone multiple times
        self.check_interval = 2  # Check every 2 seconds

    def is_captcha_present(self, timeout=5):
        """Check if CAPTCHA is present using multiple indicators, including iframes."""
        try:
            print(f"🔍 Checking for CAPTCHA (timeout: {timeout}s)...")
            time.sleep(timeout)

            # Check for text indicator
            captcha_text = "Please confirm you're a human"
            if self.browser.is_text_visible(captcha_text):
                print("✓ CAPTCHA detected via text")
                return True

            # Check for container elements
            container_selectors = [
                "#sec-if-cpt-container",  # Updated from HTML
                "#sec-container",
                ".behavioral-content"
            ]
            for selector in container_selectors:
                try:
                    if self.browser.is_element_visible(selector):
                        print(f"✓ CAPTCHA detected via container: {selector}")
                        return True
                except:
                    continue

            # Check for iframes
            iframe_selectors = [
                "iframe[src*='captcha']",
                "iframe[title*='recaptcha']",
                "iframe[role='presentation']",
                "iframe"  # Fallback: any iframe
            ]
            for selector in iframe_selectors:
                try:
                    iframes = self.browser.find_elements(selector)
                    for iframe in iframes:
                        try:
                            if iframe.is_displayed():
                                print(f"✓ CAPTCHA detected via iframe: {selector}")
                                self.browser.switch_to_frame(iframe)
                                checkbox_selectors = [
                                    '//*[@id="robot-checkbox"]',
                                    '//input[@type="checkbox"]',
                                    '//input[contains(@id, "checkbox")]',
                                    '//input[@value="true"]'
                                ]
                                for checkbox_selector in checkbox_selectors:
                                    try:
                                        if self.browser.is_element_visible(checkbox_selector):
                                            print(f"✓ CAPTCHA checkbox found in iframe: {checkbox_selector}")
                                            self.browser.switch_to_default_content()
                                            return True
                                    except:
                                        continue
                                self.browser.switch_to_default_content()
                        except:
                            continue
                except:
                    continue

            # Check for checkbox directly
            checkbox_selectors = [
                '//*[@id="robot-checkbox"]',
                '//input[@type="checkbox"]',
                '//input[contains(@id, "checkbox")]',
                '//input[@value="true"]'
            ]
            for selector in checkbox_selectors:
                try:
                    if self.browser.is_element_visible(selector):
                        print(f"✓ CAPTCHA detected via checkbox: {selector}")
                        return True
                except:
                    continue

            # Check for proceed button
            proceed_selectors = [
                "#progress-button",
                ".behavioral-button",
                "xpath=//div[@id='progress-button']"
            ]
            for selector in proceed_selectors:
                try:
                    if selector.startswith("xpath="):
                        elements = self.browser.find_elements(selector[6:], by="xpath")
                    else:
                        elements = self.browser.find_elements(selector)
                    if any(elem.is_displayed() for elem in elements):
                        print(f"✓ CAPTCHA detected via proceed button: {selector}")
                        return True
                except:
                    continue

            print("✓ No CAPTCHA detected")
            return False

        except Exception as e:
            print(f"❌ Error checking CAPTCHA presence: {e}")
            # Save page source for debugging
            page_source = self.browser.get_page_source()
            with open(f"debug_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("📝 Saved page source for debugging")
            return False
    def click_checkbox_if_unchecked(self):
        """Click the 'I'm not a robot' checkbox if not checked, with enhanced iframe and visibility handling."""
        try:
            print("🔍 Checking for checkbox...")

            # Step 1: Check for iframes containing the CAPTCHA
            iframe_selectors = [
                "iframe[src*='captcha']",
                "iframe[title*='recaptcha']",
                "iframe[role='presentation']",
                "iframe",  # Fallback: any iframe
            ]
            iframe_found = False
            for selector in iframe_selectors:
                try:
                    iframes = self.browser.find_elements(selector)
                    for iframe in iframes:
                        try:
                            if iframe.is_displayed():
                                print(f"✓ Found visible iframe: {selector}")
                                self.browser.switch_to_frame(iframe)
                                iframe_found = True
                                break
                        except:
                            continue
                    if iframe_found:
                        break
                except:
                    continue

            # Step 2: Define checkbox selectors
            checkbox_selectors = [
                '//*[@id="robot-checkbox"]',  # Primary ID-based XPath
                '//input[@type="checkbox"]',  # Fallback: any checkbox
                '//input[contains(@id, "checkbox")]',  # Fallback: partial ID match
                '//input[@value="true"]',  # Fallback: match value attribute from HTML
            ]

            # Step 3: Try each selector with extended timeout and visibility checks
            checkbox_found = False
            for selector in checkbox_selectors:
                try:
                    print(f"🔍 Trying selector: {selector}")
                    # Wait for element to be present in DOM (not necessarily visible)
                    if not self.browser.wait_for_element_present(selector, timeout=20):
                        print(f"⚠️ Element not present: {selector}")
                        continue

                    # Get the element
                    element = self.browser.find_element(selector)

                    # Ensure element is in viewport
                    self.browser.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        element
                    )
                    time.sleep(1)

                    # Check visibility explicitly
                    if not element.is_displayed():
                        print(f"⚠️ Element not visible: {selector}")
                        continue

                    checkbox_found = True
                    print(f"✓ Checkbox found with selector: {selector}")

                    # Check if already checked
                    if self.browser.is_checked(selector):
                        print("✓ Checkbox already checked")
                        if iframe_found:
                            self.browser.switch_to_default_content()
                        return True

                    # Attempt to click using JavaScript
                    self.browser.execute_script("arguments[0].click();", element)
                    time.sleep(1)

                    # Verify the click
                    if self.browser.is_checked(selector):
                        print("✓ Successfully checked the checkbox")
                        if iframe_found:
                            self.browser.switch_to_default_content()
                        return True
                    else:
                        print(f"❌ Checkbox click failed with selector: {selector}")
                        continue

                except Exception as e:
                    print(f"⚠️ Error with selector {selector}: {e}")
                    continue

            # Step 4: If no checkbox was found
            if not checkbox_found:
                print("❌ Checkbox not found with any selector")
                # Save page source for debugging
                page_source = self.browser.get_page_source()
                with open(f"debug_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                print("📝 Saved page source for debugging")
                if iframe_found:
                    self.browser.switch_to_default_content()
                return False

            if iframe_found:
                self.browser.switch_to_default_content()
            return False

        except Exception as e:
            print(f"❌ Critical error clicking checkbox: {e}")
            if iframe_found:
                self.browser.switch_to_default_content()
            # Save page source for debugging
            page_source = self.browser.get_page_source()
            with open(f"debug_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("📝 Saved page source for debugging")
            return False
    def wait_for_proceed_enabled(self, timeout=15):
        """Wait for the Proceed button to become enabled, handling iframes."""
        try:
            print("⏳ Waiting for Proceed button to enable...")

            # Check for iframes
            iframe_selectors = [
                "iframe[src*='captcha']",
                "iframe[title*='recaptcha']",
                "iframe[role='presentation']",
                "iframe"
            ]
            iframe_found = False
            for selector in iframe_selectors:
                try:
                    iframes = self.browser.find_elements(selector)
                    for iframe in iframes:
                        if iframe.is_displayed():
                            print(f"✓ Found visible iframe: {selector}")
                            self.browser.switch_to_frame(iframe)
                            iframe_found = True
                            break
                    if iframe_found:
                        break
                except:
                    continue

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check for disabled button
                    disabled_elements = self.browser.find_elements(".progress-btn-disabled")
                    if not disabled_elements or not any(elem.is_displayed() for elem in disabled_elements):
                        print("✓ Proceed button is enabled (no disabled class)")
                        if iframe_found:
                            self.browser.switch_to_default_content()
                        return True

                    # Check for enabled button
                    enabled_selectors = [
                        ".progress-btn",
                        "#progress-button",
                        "xpath=//div[@id='progress-button']",
                        "xpath=//div[contains(@class, 'behavioral-button') and not(contains(@class, 'progress-btn-disabled'))]"
                    ]
                    for selector in enabled_selectors:
                        try:
                            if selector.startswith("xpath="):
                                elements = self.browser.find_elements(selector[6:], by="xpath")
                            else:
                                elements = self.browser.find_elements(selector)
                            for element in elements:
                                if element.is_displayed():
                                    print(f"✓ Proceed button is enabled: {selector}")
                                    if iframe_found:
                                        self.browser.switch_to_default_content()
                                    return True
                        except:
                            continue

                except Exception as e:
                    print(f"⚠️ Error checking button state: {e}")
                time.sleep(0.5)

            print("❌ Timeout waiting for Proceed button to enable")
            if iframe_found:
                self.browser.switch_to_default_content()
            return False

        except Exception as e:
            print(f"❌ Error waiting for Proceed button: {e}")
            if iframe_found:
                self.browser.switch_to_default_content()
            return False
    def click_proceed_button(self):
        """Click the Proceed button, handling iframes and visibility."""
        try:
            print("🔍 Attempting to click Proceed button...")

            # Step 1: Check for iframes
            iframe_selectors = [
                "iframe[src*='captcha']",
                "iframe[title*='recaptcha']",
                "iframe[role='presentation']",
                "iframe"  # Fallback: any iframe
            ]
            iframe_found = False
            for selector in iframe_selectors:
                try:
                    iframes = self.browser.find_elements(selector)
                    for iframe in iframes:
                        try:
                            if iframe.is_displayed():
                                print(f"✓ Found visible iframe: {selector}")
                                self.browser.switch_to_frame(iframe)
                                iframe_found = True
                                break
                        except:
                            continue
                    if iframe_found:
                        break
                except:
                    continue

            # Step 2: Define Proceed button selectors
            proceed_selectors = [
                "#progress-button",  # ID-based selector
                ".behavioral-button.progress-btn",  # Specific class when enabled
                "xpath=//div[@id='progress-button']",  # XPath for ID
                "xpath=//div[contains(@class, 'behavioral-button') and not(contains(@class, 'progress-btn-disabled'))]"  # XPath for enabled button
            ]

            # Step 3: Try each selector
            for selector in proceed_selectors:
                try:
                    print(f"🔍 Trying selector: {selector}")
                    if selector.startswith("xpath="):
                        elements = self.browser.find_elements(selector[6:], by="xpath")
                    else:
                        elements = self.browser.find_elements(selector)

                    for element in elements:
                        try:
                            # Ensure element is in viewport
                            self.browser.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                element
                            )
                            time.sleep(1)

                            # Check visibility
                            if not element.is_displayed():
                                print(f"⚠️ Element not visible: {selector}")
                                continue

                            print(f"✓ Found clickable Proceed button: {selector}")
                            # Use JavaScript click for reliability
                            self.browser.execute_script("arguments[0].click();", element)
                            print("✓ Successfully clicked Proceed button")
                            if iframe_found:
                                self.browser.switch_to_default_content()
                            return True

                        except Exception as e:
                            print(f"⚠️ Error clicking element with selector {selector}: {e}")
                            continue

                except Exception as e:
                    print(f"⚠️ Error finding elements with selector {selector}: {e}")
                    continue

            # Step 4: If no button was found
            print("❌ Could not find clickable Proceed button")
            # Save page source for debugging
            page_source = self.browser.get_page_source()
            # with open(f"debug_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
            #     f.write(page_source)
            print("📝 Saved page source for debugging")
            # Save screenshot
            # self.browser.save_screenshot(f"debug_screenshot_{int(time.time())}.png")
            print("📸 Saved screenshot for debugging")
            if iframe_found:
                self.browser.switch_to_default_content()
            return False

        except Exception as e:
            print(f"❌ Critical error clicking Proceed button: {e}")
            if iframe_found:
                self.browser.switch_to_default_content()
            # Save debugging info
            page_source = self.browser.get_page_source()
            # with open(f"debug_page_source_{int(time.time())}.html", "w", encoding="utf-8") as f:
            #     f.write(page_source)
            print("📝 Saved page source for debugging")
            # self.browser.save_screenshot(f"debug_screenshot_{int(time.time())}.png")
            print("📸 Saved screenshot for debugging")
            return False
    def verify_captcha_resolved(self, verification_timeout=5):
        """
        Verify that CAPTCHA is actually resolved by checking multiple times.
        Returns True if CAPTCHA is confirmed gone, False if it's still there or reappeared.
        """
        try:
            checks_passed = 0
            checks_needed = self.verification_checks

            print(f"🔍 Verifying CAPTCHA resolution ({checks_needed} checks)...")

            for i in range(checks_needed):
                time.sleep(verification_timeout / checks_needed)

                if not self.is_captcha_present(timeout=1):
                    checks_passed += 1
                    print(f"  ✓ Check {i+1}/{checks_needed}: CAPTCHA not detected")
                else:
                    print(f"  ❌ Check {i+1}/{checks_needed}: CAPTCHA still present!")
                    return False

            print(f"✅ CAPTCHA verified as resolved ({checks_passed}/{checks_needed} checks passed)")
            return True

        except Exception as e:
            print(f"❌ Error verifying CAPTCHA resolution: {e}")
            return False

    def solve_captcha_single_attempt(self):
        """
        Single CAPTCHA solve attempt.
        Returns: (success, needs_retry, error_message)
        """
        try:
            print("\n" + "="*60)
            print("🤖 CAPTCHA SOLVE ATTEMPT")
            print("="*60)

            # Step 1: Verify CAPTCHA is present
            if not self.is_captcha_present(timeout=5):
                print("✓ No CAPTCHA detected")
                return (True, False, "")

            print("⚠️  CAPTCHA detected - beginning solve process...")

            # Step 2: Click checkbox
            if not self.click_checkbox_if_unchecked():
                return (False, True, "Failed to click checkbox")

            time.sleep(1)

            # Step 3: Wait for Proceed button to enable
            if not self.wait_for_proceed_enabled(timeout=15):
                return (False, True, "Proceed button did not enable")

            time.sleep(1)

            # Step 4: Click Proceed button
            if not self.click_proceed_button():
                return (False, True, "Failed to click Proceed button")

            print("⏳ Waiting for CAPTCHA processing (up to 45 seconds)...")

            # Step 5: Wait and monitor for resolution
            start_time = time.time()
            last_check_time = start_time

            while time.time() - start_time < self.proceed_timeout:
                current_time = time.time()

                # Check every 2 seconds
                if current_time - last_check_time >= self.check_interval:
                    elapsed = int(current_time - start_time)
                    remaining = int(self.proceed_timeout - elapsed)

                    print(f"  ⏱️  Checking... ({elapsed}s elapsed, {remaining}s remaining)")

                    # Check if CAPTCHA is gone
                    if not self.is_captcha_present(timeout=1):
                        print("  ✓ CAPTCHA appears to be resolved!")

                        # Verify it's actually gone (not just temporarily hidden)
                        if self.verify_captcha_resolved(verification_timeout=6):
                            print("✅ CAPTCHA SUCCESSFULLY SOLVED!")
                            return (True, False, "")
                        else:
                            print("⚠️  CAPTCHA reappeared during verification - needs retry")
                            return (False, True, "CAPTCHA reappeared after initial resolution")

                    # Check if new CAPTCHA appeared (checkbox is unchecked again)
                    try:
                        checkbox_xpath = '//*[@id="robot-checkbox"]'
                        if self.browser.is_element_visible(checkbox_xpath):
                            if not self.browser.is_checked(checkbox_xpath):
                                print("⚠️  New CAPTCHA appeared - checkbox is unchecked")
                                return (False, True, "New CAPTCHA appeared")
                    except:
                        pass

                    last_check_time = current_time

                time.sleep(0.5)

            # Timeout reached
            print(f"⏱️  Timeout reached ({self.proceed_timeout}s)")

            # Final check - is CAPTCHA still there?
            if self.is_captcha_present(timeout=2):
                print("❌ CAPTCHA still present after timeout - needs retry")
                return (False, True, "Timeout waiting for CAPTCHA resolution")
            else:
                print("✓ CAPTCHA not detected after timeout - assuming success")
                return (True, False, "")

        except Exception as e:
            error_msg = f"Exception during CAPTCHA solve: {str(e)}"
            print(f"❌ {error_msg}")
            return (False, True, error_msg)

    def solve_captcha(self):
        """
        Main CAPTCHA solving method with multiple attempts and persistent monitoring.
        Returns True if CAPTCHA is solved, False if all attempts failed.
        """
        print("\n" + "🔐" * 30)
        print("CAPTCHA RESOLUTION PROCESS STARTED")
        print("🔐" * 30)

        for attempt in range(1, self.max_solve_attempts + 1):
            print(f"\n{'='*60}")
            print(f"ATTEMPT {attempt}/{self.max_solve_attempts}")
            print(f"{'='*60}")

            success, needs_retry, error_msg = self.solve_captcha_single_attempt()

            if success:
                print(f"\n✅ CAPTCHA SOLVED SUCCESSFULLY ON ATTEMPT {attempt}!")

                # Extra safety: Wait a bit and check one more time
                print("🔍 Final safety check...")
                time.sleep(3)

                if not self.is_captcha_present(timeout=2):
                    print("✅ Final check passed - CAPTCHA is definitely solved!")
                    return True
                else:
                    print("⚠️  CAPTCHA reappeared during final check - continuing attempts...")
                    continue

            if not needs_retry:
                print(f"\n❌ CAPTCHA solve failed (non-retriable): {error_msg}")
                return False

            # Retriable error - prepare for next attempt
            if attempt < self.max_solve_attempts:
                wait_time = min(3 + attempt, 8)  # Progressive wait: 4, 5, 6, 7, 8 seconds
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

                # Refresh page if multiple failures
                if attempt >= 3:
                    print("🔄 Refreshing page due to multiple failures...")
                    self.browser.refresh()
                    time.sleep(4)

        print(f"\n❌ CAPTCHA SOLVE FAILED - ALL {self.max_solve_attempts} ATTEMPTS EXHAUSTED")
        return False

    def monitor_and_solve_if_present(self, context=""):
        """
        Check for CAPTCHA and solve it if present.
        This can be called at any point during processing.

        Args:
            context: String describing where this check is happening (e.g., "after_login", "on_claims_page")

        Returns:
            True if no CAPTCHA or CAPTCHA solved successfully
            False if CAPTCHA present and could not be solved
        """
        print(f"\n🔍 CAPTCHA Check ({context})...")

        if self.is_captcha_present(timeout=3):
            print(f"⚠️  CAPTCHA detected at: {context}")
            return self.solve_captcha()
        else:
            print(f"✓ No CAPTCHA at: {context}")
            return True


# Integration example for the main processor
def integrate_improved_captcha(processor_instance):
    """
    This function shows how to integrate the improved CAPTCHA handler
    into the existing IntegratedMedicareProcessor class.
    """

    # Initialize the improved handler
    captcha_handler = ImprovedCaptchaHandler(processor_instance)

    # Replace the old methods
    processor_instance.is_captcha_present = captcha_handler.is_captcha_present
    processor_instance.solve_captcha = captcha_handler.solve_captcha

    # Add the new monitoring method
    processor_instance.monitor_and_solve_captcha = captcha_handler.monitor_and_solve_if_present

    return processor_instance
