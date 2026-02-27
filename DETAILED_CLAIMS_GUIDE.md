# 📊 Detailed Claims Extractor - Complete Guide

## What This Does

This test script extracts **COMPLETE claim information** including:
- ✅ All services with procedure codes
- ✅ All financial amounts (charged, approved, deductible, coinsurance)
- ✅ Provider details
- ✅ Claim processing dates
- ✅ Everything saved as JSON inside CSV cells

**Perfect for:** Testing before running on 150 leads, analyzing specific accounts, getting complete claim data

---

## 🚀 Quick Start

### Step 1: Configure the Test

Open `test_detailed_claims_extractor.py` and edit:

```python
# ===================== TEST CONFIG ===================== #
TEST_USERNAME = "john_doe@gmail.com"     # ← YOUR USERNAME
TEST_PASSWORD = "MyPassword123!"         # ← YOUR PASSWORD
MAX_CLAIMS_TO_EXTRACT = 5                # ← HOW MANY CLAIMS (from latest)
OUTPUT_FILE = "detailed_claims_test_output.csv"
```

### Step 2: Run

```bash
python test_detailed_claims_extractor.py
```

### Step 3: Check Results

Open `detailed_claims_test_output.csv` in Excel

---

## 📋 What You'll See

### Console Output:

```
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
  → Solving CAPTCHA...
  → Verifying login...
✅ Login successful!

📄 Navigating to claims page...
✅ Claims page loaded - Found 23 initial claims

🔍 Scanning claims to find valid doctors...
  [1] SMITH, JOHN - 12/30/25 → ✅ VALID
  [2] ABC MEDICAL CENTER - 12/28/25 → ❌ SKIP (company)
  [3] JONES, MARY - 12/15/25 → ✅ VALID
  [4] DOE, JANE - 12/10/25 → ❌ Bad specialty: Dentistry
  [5] BROWN, ROBERT - 11/28/25 → ✅ VALID
  [6] DENTAL CLINIC LLC - 11/20/25 → ❌ SKIP (company)
  [7] DAVIS, WILLIAM - 11/15/25 → ✅ VALID
  [8] WILSON, SARAH - 11/05/25 → ✅ VALID

✅ Found 5 valid claims to extract
================================================================================

📥 Extracting claim 1/5: SMITH, JOHN
  → Extracting all data...
  ✅ Extracted: 2 services, Total charged: $275.00

📥 Extracting claim 2/5: JONES, MARY
  → Extracting all data...
  ✅ Extracted: 1 services, Total charged: $150.00

📥 Extracting claim 3/5: BROWN, ROBERT
  → Extracting all data...
  ✅ Extracted: 3 services, Total charged: $425.00

📥 Extracting claim 4/5: DAVIS, WILLIAM
  → Extracting all data...
  ✅ Extracted: 1 services, Total charged: $200.00

📥 Extracting claim 5/5: WILSON, SARAH
  → Extracting all data...
  ✅ Extracted: 2 services, Total charged: $350.00

💾 Saving 5 claims to CSV...
✅ Saved successfully

================================================================================
✅ EXTRACTION COMPLETE
================================================================================
Total claims extracted: 5
Output saved to: detailed_claims_test_output.csv
================================================================================
```

---

## 📊 Output CSV Structure

### Columns:

| Column | Description | Example |
|--------|-------------|---------|
| claim_number | Claim ID from Medicare | 1126005184730 |
| provider | Doctor name | MARGULIS, MICHAEL E. |
| provider_address | Full address | 123 GROVE AVE, STE 214, CEDARHURST, NY 11516-2302 |
| date_of_service | When service occurred | 12/30/25 |
| claim_processed_on | When claim was processed | 01/07/26 |
| service_count | Number of services | 2 |
| total_amount_charged | Total provider charged | $275.00 |
| total_medicare_approved | Total Medicare approved | $167.33 |
| total_you_may_be_billed | What patient owes | $33.47 |
| **complete_claim_json** | **FULL CLAIM DATA AS JSON** | (see below) |

---

## 🎯 The JSON Data (complete_claim_json column)

Each cell contains a complete JSON object with ALL claim details:

### JSON Structure:

```json
{
  "basic_info": {
    "date_of_service": "12/30/25",
    "provider": "MARGULIS, MICHAEL E.",
    "provider_address": "123 GROVE AVE, STE 214, CEDARHURST, NY 11516-2302",
    "claim_processed_on": "01/07/26",
    "practicing_providers": "Not available",
    "claim_number": "1126005184730"
  },
  
  "services": [
    {
      "service_name": "EXTENDED EXAM OF THE BACK PART OF THE EYE WITH RETINAL DRAWING",
      "procedure_code": "92201",
      "quantity": "1",
      "provider_charged": "$75.00",
      "medicare_approved": "$27.44",
      "applied_to_deductible": "$0.00",
      "coinsurance": "$5.49",
      "you_may_be_billed": "$5.49"
    },
    {
      "service_name": "ESTABLISHED PATIENT COMPLETE EXAM OF VISUAL SYSTEM",
      "procedure_code": "92014",
      "quantity": "1",
      "provider_charged": "$200.00",
      "medicare_approved": "$139.89",
      "applied_to_deductible": "$0.00",
      "coinsurance": "$27.98",
      "you_may_be_billed": "$27.98"
    }
  ],
  
  "summary": {
    "total_amount_charged": "$275.00",
    "total_medicare_approved": "$167.33",
    "blood_deductible": "$0.00",
    "physical_therapy_charges": "$0.00",
    "psychiatric_charges": "$0.00",
    "occupational_therapy_charges": "$0.00",
    "total_patient_paid_provider": "$0.00",
    "total_medicare_paid_you": "$0.00",
    "total_medicare_paid_provider": "$131.18",
    "total_applied_to_deductible": "$0.00",
    "total_coinsurance": "$33.47",
    "total_you_may_be_billed": "$33.47"
  },
  
  "validation_info": {
    "provider_from_card": "MARGULIS, MICHAEL E.",
    "date_from_card": "12/30/25"
  }
}
```

### How to Read JSON in Excel:

**Option 1: View in Excel**
- Double-click the cell to see full JSON
- Copy to text editor for better formatting

**Option 2: Parse with Python**
```python
import pandas as pd
import json

df = pd.read_csv('detailed_claims_test_output.csv')
for idx, row in df.iterrows():
    claim_json = json.loads(row['complete_claim_json'])
    print(claim_json['basic_info']['provider'])
    for service in claim_json['services']:
        print(f"  - {service['service_name']} ({service['procedure_code']})")
```

**Option 3: Use Excel Power Query**
- Data → Get Data → From File → From JSON
- Select the complete_claim_json column

---

## 🎛️ Configuration Options

### Extract More or Fewer Claims

```python
MAX_CLAIMS_TO_EXTRACT = 1   # Just 1 claim (fastest)
MAX_CLAIMS_TO_EXTRACT = 5   # 5 claims (good for testing)
MAX_CLAIMS_TO_EXTRACT = 10  # 10 claims
MAX_CLAIMS_TO_EXTRACT = 99  # All valid claims (slower)
```

### Change Output File

```python
OUTPUT_FILE = "my_test_results.csv"
OUTPUT_FILE = "claims_january_2026.csv"
```

### Change State for Validation

Edit line 229 in the script:
```python
# Current:
is_valid, reason = self.validate_doctor(provider_name, "NY")

# Change to your state:
is_valid, reason = self.validate_doctor(provider_name, "FL")
is_valid, reason = self.validate_doctor(provider_name, "CA")
```

---

## 📈 What Gets Extracted

### Basic Information (6 fields)
1. ✅ Date of service
2. ✅ Provider name
3. ✅ Provider address (full, multi-line combined)
4. ✅ Claim processed on
5. ✅ Practicing providers
6. ✅ Claim number

### Services (7 fields per service)
For **each service** in the claim:
1. ✅ Service name (full description)
2. ✅ Procedure code (CPT code)
3. ✅ Quantity
4. ✅ Provider charged amount
5. ✅ Medicare approved amount
6. ✅ Applied to deductible
7. ✅ Coinsurance
8. ✅ You may be billed amount

### Summary (12 financial fields)
1. ✅ Total amount charged
2. ✅ Total Medicare approved
3. ✅ Blood deductible
4. ✅ Physical therapy charges
5. ✅ Psychiatric charges
6. ✅ Occupational therapy charges
7. ✅ Total patient paid provider
8. ✅ Total Medicare paid you
9. ✅ Total Medicare paid provider
10. ✅ Total applied to deductible
11. ✅ Total coinsurance
12. ✅ Total you may be billed

**Total: 25+ data points per claim!**

---

## 🔄 Processing Flow

```
1. Login to account
    ↓
2. Navigate to claims page
    ↓
3. Scan all visible claims
    ↓
4. FOR EACH CLAIM:
    ├─ Extract provider name from card
    ├─ Skip if company
    ├─ Validate doctor (NPI + PECOS)
    ├─ If VALID:
    │   ├─ Add to extraction list
    │   └─ Continue until MAX_CLAIMS reached
    └─ If INVALID:
        └─ Skip, continue to next
    ↓
5. FOR EACH VALID CLAIM:
    ├─ Click "Open claim details"
    ├─ Extract complete data:
    │   ├─ Basic info
    │   ├─ All services
    │   └─ Financial summary
    ├─ Navigate back to claims list
    └─ Continue to next
    ↓
6. Save all claims to CSV
    ↓
DONE
```

---

## 📸 Example Output File

**detailed_claims_test_output.csv:**

```csv
claim_number,provider,provider_address,date_of_service,service_count,total_amount_charged,complete_claim_json
1126005184730,MARGULIS MICHAEL E.,"123 GROVE AVE, STE 214, CEDARHURST, NY 11516-2302",12/30/25,2,$275.00,"{""basic_info"":{...},""services"":[{...},{...}],""summary"":{...}}"
1126005184731,SMITH JOHN,"456 MAIN ST, MIAMI, FL 33101",12/28/25,1,$150.00,"{""basic_info"":{...},""services"":[{...}],""summary"":{...}}"
...
```

When you open in Excel:
- Easy to read: claim_number, provider, totals
- Complete data: complete_claim_json cell (double-click to expand)

---

## 🎯 Use Cases

### 1. Test Before Full Run
```python
MAX_CLAIMS_TO_EXTRACT = 2  # Just 2 claims
```
Run to verify everything works

### 2. Analyze Specific Account
```python
TEST_USERNAME = "specific_patient@example.com"
MAX_CLAIMS_TO_EXTRACT = 99  # Extract all valid claims
```
Get complete claim history for one patient

### 3. Recent Claims Only
```python
MAX_CLAIMS_TO_EXTRACT = 5
```
Get just the 5 most recent valid claims

### 4. Audit/Verify Data
Extract claims with full details to verify:
- Procedure codes are correct
- Billing amounts match records
- Provider information is accurate

---

## 🔍 How It Validates Doctors

**Only extracts claims from VALID doctors:**

```
1. Check if provider name is company
   └─ Contains: LLC, INC, CENTER, CLINIC, etc.
   └─ If YES → SKIP

2. Look up in NPI Registry
   └─ Search by name + state
   └─ If NOT FOUND → SKIP

3. Validate taxonomy (specialty)
   ├─ GOOD specialty (Cardiologist, etc.) → ✅ VALID
   ├─ CN Eligible (Chiropractor, etc.) → ✅ VALID
   └─ BAD specialty (Dentist, etc.) → SKIP

4. If VALID:
   └─ Extract complete claim details
```

**Result:** Only gets detailed data from doctors you actually care about!

---

## 📊 Data Extraction Example

### Claim Card (What you see on claims list):
```
┌────────────────────────────────┐
│ MARGULIS, MICHAEL E.           │
│ Date: 12/30/25                 │
│ Amount: $275.00                │
│ [Open Claim Details]           │
└────────────────────────────────┘
```

### Claim Details Page (What script extracts):
```
┌─────────────────────────────────────────────────────────┐
│ Date of service: 12/30/25                               │
│ Provider: MARGULIS, MICHAEL E.                          │
│ Provider address: 123 GROVE AVE, STE 214, CEDARHURST   │
│ Claim processed on: 01/07/26                            │
│ Claim number: 1126005184730                             │
│                                                         │
│ SERVICES:                                               │
│ ┌─────────────────────────────────────────────────┐    │
│ │ Service: EXTENDED EXAM... (92201)               │    │
│ │ Qty: 1                                          │    │
│ │ Provider charged: $75.00                        │    │
│ │ Medicare approved: $27.44                       │    │
│ │ Coinsurance: $5.49                              │    │
│ │ You may be billed: $5.49                        │    │
│ └─────────────────────────────────────────────────┘    │
│                                                         │
│ ┌─────────────────────────────────────────────────┐    │
│ │ Service: ESTABLISHED PATIENT EXAM... (92014)    │    │
│ │ Qty: 1                                          │    │
│ │ Provider charged: $200.00                       │    │
│ │ Medicare approved: $139.89                      │    │
│ │ Coinsurance: $27.98                             │    │
│ │ You may be billed: $27.98                       │    │
│ └─────────────────────────────────────────────────┘    │
│                                                         │
│ SUMMARY:                                                │
│ Total amount charged: $275.00                           │
│ Total Medicare approved: $167.33                        │
│ Total coinsurance: $33.47                               │
│ Total you may be billed: $33.47                         │
│ Total Medicare paid provider: $131.18                   │
│ (+ 7 more summary fields)                               │
└─────────────────────────────────────────────────────────┘
```

**ALL of this → Saved as JSON in one CSV cell!**

---

## 💡 Advanced Usage

### Extract from Multiple Accounts

Create a loop version:

```python
# In test_detailed_claims_extractor.py, modify:

accounts = [
    ("user1@example.com", "pass1", "FL"),
    ("user2@example.com", "pass2", "CA"),
    ("user3@example.com", "pass3", "NY")
]

for username, password, state in accounts:
    # Login and extract
    # Save to separate CSV per account
```

### Filter by Date Range

Add date filtering:

```python
# Only extract claims from last 3 months:
from datetime import date, timedelta

threshold = date.today() - timedelta(days=90)
# Skip claims older than threshold
```

### Extract Specific Procedure Codes

Filter by service type:

```python
# Only extract claims with specific procedures:
target_codes = ['92014', '92201', '99213']

if any(code in service['procedure_code'] for code in target_codes):
    # Extract this claim
```

---

## 🆚 Comparison: Test Script vs. Main Processor

| Feature | Main Processor | Test Script |
|---------|----------------|-------------|
| Purpose | Process 150 leads | Test/analyze 1 account |
| Input | CSV with many accounts | Single username/password |
| Output | Consolidated results | Detailed claim JSONs |
| Speed | Optimized for bulk | Verbose logging |
| Data depth | Provider summary | Complete claim details |
| Threading | 6 parallel threads | Single thread |
| Validation | Full taxonomy check | Quick validation |
| Claims extracted | All valid in 9 months | Specified count only |

---

## 🔧 Troubleshooting

### Error: "Please configure TEST_USERNAME"
**Fix:** Edit the config at top of test file with real credentials

### Error: "No valid doctors found"
**Issue:** All claims are from companies or bad specialties
**Fix:** 
- Check the scan output - what does it show?
- Adjust MAX_CLAIMS_TO_EXTRACT to scan more claims
- Change state if needed

### Claims Not Loading
**Issue:** Account has no claims
**Fix:** Try different account that has recent claims

### JSON Looks Truncated in Excel
**Not an error!** Excel displays long text with "..."
**To see full JSON:**
- Double-click the cell
- Or copy cell contents to text editor
- Or use Python to parse the CSV

### Want More Claims
```python
MAX_CLAIMS_TO_EXTRACT = 20  # Increase this
```

---

## 📝 Example Use Cases

### Case 1: Quick Test
"I want to test extraction with just 1 claim"

```python
TEST_USERNAME = "test@example.com"
TEST_PASSWORD = "TestPass123"
MAX_CLAIMS_TO_EXTRACT = 1
```

**Runtime:** ~2-3 minutes  
**Output:** 1 row with complete JSON

### Case 2: Recent Activity
"Get last 10 valid claims for analysis"

```python
MAX_CLAIMS_TO_EXTRACT = 10
```

**Runtime:** ~10-15 minutes  
**Output:** Up to 10 rows with complete data

### Case 3: Full Extraction
"Get all valid claims from last 9 months"

```python
MAX_CLAIMS_TO_EXTRACT = 999  # No limit
```

**Runtime:** ~30-60 minutes (depends on claim count)  
**Output:** All valid claims with complete details

---

## 🎨 Excel Tips

### View JSON Nicely

1. **Copy cell with JSON**
2. **Paste into:** https://jsonformatter.org/
3. **View formatted JSON**

### Extract Specific Fields

Use Excel formulas to parse JSON (Excel 2016+):

```excel
// Get provider name from JSON cell A2:
=FILTERXML("<t><s>" & SUBSTITUTE(A2, ",", "</s><s>") & "</s></t>", "//s[contains(.,'provider')]")
```

### Convert JSON to Columns

1. Copy complete_claim_json column
2. Use https://json-csv.com/
3. Convert JSON to separate columns
4. Import back to Excel

---

## 🚀 Next Steps

### After Testing

1. **Verify output looks good** - Check CSV, validate JSON is complete
2. **Test with different accounts** - Make sure it works across accounts
3. **Integrate into main processor** (if needed) - Add detailed extraction to bulk script

### Integrate Detailed Extraction into Main Processor

If you want to add this to the 150-lead processor:

1. The new `extract_complete_claim_details()` function is already in `integrated_medicare_processor.py`
2. You'd need to modify `process_claims_with_taxonomy_evaluation()` to use it
3. Add `complete_claim_json` column to the main output CSV

**Want me to integrate it?** Let me know!

---

## 📋 Complete Field List

### All 25+ Fields Extracted:

**Basic Info (6):**
- date_of_service
- provider
- provider_address  
- claim_processed_on
- practicing_providers
- claim_number

**Per Service (8 × N services):**
- service_name
- procedure_code
- quantity
- provider_charged
- medicare_approved
- applied_to_deductible
- coinsurance
- you_may_be_billed

**Summary (12):**
- total_amount_charged
- total_medicare_approved
- blood_deductible
- physical_therapy_charges
- psychiatric_charges
- occupational_therapy_charges
- total_patient_paid_provider
- total_medicare_paid_you
- total_medicare_paid_provider
- total_applied_to_deductible
- total_coinsurance
- total_you_may_be_billed

---

## ⚡ Performance

| Claims | Time | Output Size |
|--------|------|-------------|
| 1 claim | ~2 min | ~2 KB |
| 5 claims | ~8 min | ~10 KB |
| 10 claims | ~15 min | ~20 KB |
| 20 claims | ~30 min | ~40 KB |

---

## 🎯 Ready to Test!

### 1. Edit config:
```python
TEST_USERNAME = "your_actual_username"
TEST_PASSWORD = "your_actual_password"  
MAX_CLAIMS_TO_EXTRACT = 5
```

### 2. Run:
```bash
python test_detailed_claims_extractor.py
```

### 3. Check:
```
detailed_claims_test_output.csv
```

**You'll get complete claim data with all services, amounts, and financial details as JSON!** 📊✨
