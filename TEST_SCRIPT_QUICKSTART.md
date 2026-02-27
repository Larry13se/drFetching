# ⚡ Test Script - 3-Step Quick Start

## What This Script Does

**Extracts COMPLETE claim details** (all services, amounts, procedure codes) for valid doctors only, saves as JSON in CSV.

---

## 🚀 How to Run (3 Steps)

### Step 1: Edit Config (30 seconds)

Open `test_detailed_claims_extractor.py`

Find this section at the top:

```python
# ===================== TEST CONFIG ===================== #
TEST_USERNAME = "your_username@example.com"  # ← CHANGE THIS
TEST_PASSWORD = "your_password"              # ← CHANGE THIS
MAX_CLAIMS_TO_EXTRACT = 5                    # ← CHANGE THIS
```

**Change to YOUR values:**

```python
TEST_USERNAME = "john_doe@gmail.com"     # Your Medicare.gov username
TEST_PASSWORD = "MyPassword123!"         # Your Medicare.gov password
MAX_CLAIMS_TO_EXTRACT = 5                # How many claims you want
```

### Step 2: Run Script (5-10 minutes)

```bash
python test_detailed_claims_extractor.py
```

### Step 3: Check Results (immediate)

Open file: `detailed_claims_test_output.csv`

**That's it!** ✅

---

## 📊 What You Get

### CSV File with These Columns:

| Column | What It Contains |
|--------|------------------|
| `claim_number` | Medicare claim ID |
| `provider` | Doctor name |
| `provider_address` | Full address |
| `date_of_service` | Service date |
| `service_count` | Number of services |
| `total_amount_charged` | Total billed |
| `total_you_may_be_billed` | What patient owes |
| **`complete_claim_json`** | **ALL claim data** |

### The complete_claim_json Cell Contains:

```json
{
  "basic_info": { ... 6 fields ... },
  "services": [ ... all services with 8 fields each ... ],
  "summary": { ... 12 financial totals ... }
}
```

**25+ data points per claim, all in one JSON object!**

---

## 🎛️ Configuration Examples

### Example 1: Quick Test (1 claim)
```python
MAX_CLAIMS_TO_EXTRACT = 1
```
**Time:** ~2 minutes  
**Gets:** 1 complete claim

### Example 2: Recent Activity (5 claims) ← Default
```python
MAX_CLAIMS_TO_EXTRACT = 5
```
**Time:** ~8 minutes  
**Gets:** 5 complete claims

### Example 3: Full Analysis (20 claims)
```python
MAX_CLAIMS_TO_EXTRACT = 20
```
**Time:** ~30 minutes  
**Gets:** 20 complete claims

### Example 4: Everything (no limit)
```python
MAX_CLAIMS_TO_EXTRACT = 999
```
**Time:** Varies (depends on claim count)  
**Gets:** All valid claims from last 9 months

---

## 🎯 What It Does Automatically

### ✅ Smart Filtering

**Automatically skips:**
- ❌ Companies (LLC, INC, CENTER, etc.)
- ❌ Bad specialties (Dentists, Podiatrists, etc.)
- ❌ Providers not in NPI Registry
- ❌ Claims older than 9 months

**Only extracts:**
- ✅ Individual doctors
- ✅ Good specialties (Cardiologists, Internal Medicine, etc.)
- ✅ Or CN eligible (Chiropractors, Nutritionists)
- ✅ Found in NPI Registry
- ✅ Recent claims (last 9 months)

### ✅ Complete Data

**Extracts everything from claim detail page:**
- Provider information
- Each service with procedure code
- All financial amounts
- Deductibles, coinsurance, totals
- Processing dates

---

## 📋 Before & After Comparison

### OLD (Main Processor):
```csv
DR1: SMITH, JOHN // 123 Main St // 1234567890 // Enrolled // Cardiology // 12/30/25 // CN: NO
```
**Data:** Basic summary (1 line)

### NEW (Test Script):
```csv
complete_claim_json: {
  "basic_info": { "date_of_service": "12/30/25", "provider": "SMITH, JOHN", ... },
  "services": [
    { "service_name": "...", "procedure_code": "92201", "provider_charged": "$75", ... },
    { "service_name": "...", "procedure_code": "92014", "provider_charged": "$200", ... }
  ],
  "summary": { "total_amount_charged": "$275", ... }
}
```
**Data:** Complete details (25+ fields)

---

## 🖥️ Live Console Example

### What You'll Actually See:

```
C:\...\DR-chase-Medicare-main> python test_detailed_claims_extractor.py

================================================================================
DETAILED CLAIMS EXTRACTOR - TEST MODE
================================================================================
Username: john_doe@gmail.com
Max claims to extract: 5
Output file: detailed_claims_test_output.csv
================================================================================

🔐 Logging in as: john_doe@gmail.com
  → Entering username...
  → Waiting for password field...
  → Entering password...
  → Clicking Sign In...
  → Verifying login...
✅ Login successful!

📄 Navigating to claims page...
✅ Claims page loaded - Found 23 initial claims

🔍 Scanning claims to find valid doctors...
  [1] MARGULIS, MICHAEL E. - 12/30/25 → ✅ VALID
  [2] ABC MEDICAL CENTER - 12/28/25 → SKIP (company)
  [3] DENTAL CARE LLC - 12/20/25 → SKIP (company)
  [4] SMITH, JOHN - 12/15/25 → ✅ VALID
  [5] JONES, MARY - 12/10/25 → ❌ Bad specialty: Dentistry
  [6] BROWN, ROBERT - 11/28/25 → ✅ VALID
  [7] DAVIS, WILLIAM - 11/20/25 → ✅ VALID
  [8] WILSON, SARAH - 11/15/25 → ✅ VALID

✅ Found 5 valid claims to extract
================================================================================

📥 Extracting claim 1/5: MARGULIS, MICHAEL E.
  → Extracting all data...
  ✅ Extracted: 2 services, Total charged: $275.00

📥 Extracting claim 2/5: SMITH, JOHN
  → Extracting all data...
  ✅ Extracted: 3 services, Total charged: $525.00

📥 Extracting claim 3/5: BROWN, ROBERT
  → Extracting all data...
  ✅ Extracted: 1 services, Total charged: $180.00

📥 Extracting claim 4/5: DAVIS, WILLIAM
  → Extracting all data...
  ✅ Extracted: 2 services, Total charged: $350.00

📥 Extracting claim 5/5: WILSON, SARAH
  → Extracting all data...
  ✅ Extracted: 4 services, Total charged: $625.00

💾 Saving 5 claims to CSV...
✅ Saved successfully

================================================================================
✅ EXTRACTION COMPLETE
================================================================================
Total claims extracted: 5
Output saved to: detailed_claims_test_output.csv
================================================================================

C:\...\DR-chase-Medicare-main>
```

---

## 📁 Output File Example

**detailed_claims_test_output.csv** opened in Excel:

### Summary View:
| claim_number | provider | date | service_count | total_charged | total_billed |
|--------------|----------|------|---------------|---------------|--------------|
| 1126005184730 | MARGULIS, M. | 12/30/25 | 2 | $275.00 | $33.47 |
| 1126005184895 | SMITH, J. | 12/15/25 | 3 | $525.00 | $104.00 |
| 1126005185123 | BROWN, R. | 11/28/25 | 1 | $180.00 | $0.00 |
| 1126005185456 | DAVIS, W. | 11/20/25 | 2 | $350.00 | $70.00 |
| 1126005185789 | WILSON, S. | 11/15/25 | 4 | $625.00 | $125.00 |

### Complete Data (complete_claim_json column):
Click any cell to see full JSON with all details!

---

## ⚠️ Important Notes

### Required Configuration

**Must change before running:**
- ✅ `TEST_USERNAME` → Your actual username
- ✅ `TEST_PASSWORD` → Your actual password

**Optional:**
- `MAX_CLAIMS_TO_EXTRACT` → Default 5 is good for testing
- `OUTPUT_FILE` → Default name is fine

### What "Valid Doctor" Means

Script only extracts claims from doctors who:
1. ✅ Are individuals (not companies/clinics)
2. ✅ Found in NPI Registry
3. ✅ Have good specialties OR are CN eligible
4. ✅ Pass basic validation criteria

**Result:** You don't waste time extracting bad claims!

### Time Expectations

| Claims | Extraction Time |
|--------|-----------------|
| 1 | ~2 min |
| 5 | ~8 min |
| 10 | ~15 min |
| 20 | ~30 min |
| 50 | ~90 min |

*Includes: Login, validation, detailed extraction, save*

---

## 🆘 Troubleshooting

### "Please configure TEST_USERNAME"
**Problem:** Didn't edit the config  
**Fix:** Change `TEST_USERNAME` and `TEST_PASSWORD` at top of file

### "Login failed"
**Problem:** Wrong credentials or CAPTCHA issue  
**Fix:** Verify username/password, run again (CAPTCHA retries)

### "No valid doctors found"
**Problem:** All claims are companies or bad specialties  
**Fix:** 
- Increase `MAX_CLAIMS_TO_EXTRACT` to scan more
- Check what was scanned in console output
- Try different account

### JSON Looks Weird in Excel
**Not a problem!** JSON is compressed in CSV  
**To view nicely:**
- Copy cell content
- Paste into: https://jsonformatter.org/
- Or use Python to parse it

---

## 🎯 Quick Decision Guide

### "Should I use test script or main processor?"

| Need | Use This |
|------|----------|
| Test if extraction works | ✅ Test script |
| Extract 1 account in detail | ✅ Test script |
| Get complete claim data | ✅ Test script |
| Process 150 leads efficiently | ❌ Main processor |
| Just need doctor names/NPIs | ❌ Main processor |
| Need detailed billing info | ✅ Test script |

---

## 📖 Summary

### What Test Script Does:
1. Logs into 1 account
2. Scans claims for valid doctors
3. Extracts complete details (services, amounts, etc.)
4. Saves as JSON in CSV

### What You Get:
- Easy-to-read CSV with key fields
- Complete claim data as JSON
- Only valid doctors
- Ready for analysis

### How Long:
- 5 claims ≈ 8 minutes
- 10 claims ≈ 15 minutes

---

## 🚀 Ready to Run!

```bash
# 1. Edit config (change username, password)
# 2. Run:
python test_detailed_claims_extractor.py

# 3. Wait ~8 minutes for 5 claims
# 4. Open: detailed_claims_test_output.csv
```

**You'll have complete claim data with all services and financial details!** ✨
