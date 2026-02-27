#!/usr/bin/env python3
"""
Test if manual login works in automated browser
If manual works but automation doesn't → timing/behavioral issue
If manual also fails → IP blocked
"""
 
import undetected_chromedriver as uc
import time
 
def test_manual_login():
    print("="*60)
    print("MANUAL LOGIN TEST IN AUTOMATED BROWSER")
    print("="*60)
   
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--enable-webgl')
    options.add_argument('--use-gl=desktop')
   
    # Don't set experimental options - uc.Chrome handles it
    driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
   
    print("\n🌐 Opening Medicare login page...")
    driver.get('https://www.medicare.gov/account/login')
   
    print("\n" + "="*60)
    print("NOW DO THIS:")
    print("="*60)
    print("1. Manually type a username and password")
    print("2. Click the login button YOURSELF")
    print("3. Watch what happens")
    print("")
    print("✅ If login WORKS → Automation timing is the issue")
    print("❌ If you get 403 → Your IP is blocked by Medicare")
    print("="*60)
   
    input("\nPress Enter after testing manual login...")
   
    # Check final URL
    final_url = driver.current_url
    print(f"\nFinal URL: {final_url}")
   
    if "/my/" in final_url:
        print("✅ LOGIN SUCCESSFUL!")
        print("   → Problem is automation timing/behavior")
        print("   → Solution: Adjust delays or use hybrid approach")
    elif "403" in driver.page_source or "Forbidden" in driver.page_source:
        print("❌ 403 FORBIDDEN")
        print("   → Problem is IP/network blocking")
        print("   → Solution: Residential proxy required")
    else:
        print("⚠️ Unknown result - check the page")
   
    input("\nPress Enter to close...")
    driver.quit()
 
if __name__ == "__main__":
    test_manual_login()
 