# Example JSON Output - Complete Claim Data

## What Gets Saved in the `complete_claim_json` Column

This is exactly what you'll see in the CSV cell for each claim.

---

## 🎯 Example 1: Eye Exam Claim

### From Your HTML Example:

**Provider:** MARGULIS, MICHAEL E.  
**Date:** 12/30/25  
**Services:** 2 (Eye exams)  
**Total:** $275.00

### JSON Output (in CSV cell):

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

---

## 🎯 Example 2: Cardiology Visit

**Provider:** SMITH, JOHN (Cardiologist)  
**Date:** 11/15/25  
**Services:** 3 (Office visit + EKG + Stress test)

```json
{
  "basic_info": {
    "date_of_service": "11/15/25",
    "provider": "SMITH, JOHN",
    "provider_address": "456 MEDICAL PLAZA, SUITE 300, MIAMI, FL 33101",
    "claim_processed_on": "11/22/25",
    "practicing_providers": "SMITH, JOHN",
    "claim_number": "1126005184895"
  },
  "services": [
    {
      "service_name": "OFFICE VISIT ESTABLISHED PATIENT",
      "procedure_code": "99213",
      "quantity": "1",
      "provider_charged": "$150.00",
      "medicare_approved": "$95.00",
      "applied_to_deductible": "$0.00",
      "coinsurance": "$19.00",
      "you_may_be_billed": "$19.00"
    },
    {
      "service_name": "ELECTROCARDIOGRAM ROUTINE WITH INTERPRETATION",
      "procedure_code": "93000",
      "quantity": "1",
      "provider_charged": "$75.00",
      "medicare_approved": "$45.00",
      "applied_to_deductible": "$0.00",
      "coinsurance": "$9.00",
      "you_may_be_billed": "$9.00"
    },
    {
      "service_name": "CARDIOVASCULAR STRESS TEST WITH PHYSICIAN SUPERVISION",
      "procedure_code": "93015",
      "quantity": "1",
      "provider_charged": "$300.00",
      "medicare_approved": "$180.00",
      "applied_to_deductible": "$50.00",
      "coinsurance": "$26.00",
      "you_may_be_billed": "$76.00"
    }
  ],
  "summary": {
    "total_amount_charged": "$525.00",
    "total_medicare_approved": "$320.00",
    "blood_deductible": "$0.00",
    "physical_therapy_charges": "$0.00",
    "psychiatric_charges": "$0.00",
    "occupational_therapy_charges": "$0.00",
    "total_patient_paid_provider": "$0.00",
    "total_medicare_paid_you": "$0.00",
    "total_medicare_paid_provider": "$245.00",
    "total_applied_to_deductible": "$50.00",
    "total_coinsurance": "$54.00",
    "total_you_may_be_billed": "$104.00"
  },
  "validation_info": {
    "provider_from_card": "SMITH, JOHN",
    "date_from_card": "11/15/25"
  }
}
```

---

## 🎯 Example 3: Single Service Claim

**Provider:** JONES, MARY (Internal Medicine)  
**Date:** 10/05/25  
**Services:** 1 (Annual wellness visit)

```json
{
  "basic_info": {
    "date_of_service": "10/05/25",
    "provider": "JONES, MARY",
    "provider_address": "789 HEALTH CENTER DR, TAMPA, FL 33602",
    "claim_processed_on": "10/12/25",
    "practicing_providers": "JONES, MARY",
    "claim_number": "1126005185123"
  },
  "services": [
    {
      "service_name": "ANNUAL WELLNESS VISIT",
      "procedure_code": "G0438",
      "quantity": "1",
      "provider_charged": "$180.00",
      "medicare_approved": "$180.00",
      "applied_to_deductible": "$0.00",
      "coinsurance": "$0.00",
      "you_may_be_billed": "$0.00"
    }
  ],
  "summary": {
    "total_amount_charged": "$180.00",
    "total_medicare_approved": "$180.00",
    "blood_deductible": "$0.00",
    "physical_therapy_charges": "$0.00",
    "psychiatric_charges": "$0.00",
    "occupational_therapy_charges": "$0.00",
    "total_patient_paid_provider": "$0.00",
    "total_medicare_paid_you": "$0.00",
    "total_medicare_paid_provider": "$180.00",
    "total_applied_to_deductible": "$0.00",
    "total_coinsurance": "$0.00",
    "total_you_may_be_billed": "$0.00"
  },
  "validation_info": {
    "provider_from_card": "JONES, MARY",
    "date_from_card": "10/05/25"
  }
}
```

---

## 📊 How to Work with This Data

### In Python:

```python
import pandas as pd
import json

# Load CSV
df = pd.read_csv('detailed_claims_test_output.csv')

# Parse first claim
first_claim = json.loads(df.iloc[0]['complete_claim_json'])

# Access data
print(f"Provider: {first_claim['basic_info']['provider']}")
print(f"Total charged: {first_claim['summary']['total_amount_charged']}")
print(f"\nServices:")
for service in first_claim['services']:
    print(f"  - {service['service_name']} ({service['procedure_code']})")
    print(f"    Charged: {service['provider_charged']}, Billed: {service['you_may_be_billed']}")
```

**Output:**
```
Provider: MARGULIS, MICHAEL E.
Total charged: $275.00

Services:
  - EXTENDED EXAM OF THE BACK PART OF THE EYE WITH RETINAL DRAWING (92201)
    Charged: $75.00, Billed: $5.49
  - ESTABLISHED PATIENT COMPLETE EXAM OF VISUAL SYSTEM (92014)
    Charged: $200.00, Billed: $27.98
```

### In Excel:

**Get specific value from JSON:**

```excel
// Assuming JSON is in cell A2
// This is complex - easier to use Python or Power Query
```

**Better approach:** Use Power Query:
1. Data → Get Data → From Table/Range
2. Select complete_claim_json column
3. Transform → Parse as JSON
4. Expand columns

---

## 🎯 Real CSV Output Example

**File: detailed_claims_test_output.csv**

### Row 1:
```
claim_number: 1126005184730
provider: MARGULIS, MICHAEL E.
provider_address: 123 GROVE AVE, STE 214, CEDARHURST, NY 11516-2302
date_of_service: 12/30/25
claim_processed_on: 01/07/26
service_count: 2
total_amount_charged: $275.00
total_medicare_approved: $167.33
total_you_may_be_billed: $33.47
complete_claim_json: {"basic_info":{"date_of_service":"12/30/25",...},"services":[{...},{...}],"summary":{...}}
```

### Row 2:
```
claim_number: 1126005184895
provider: SMITH, JOHN
provider_address: 456 MEDICAL PLAZA, SUITE 300, MIAMI, FL 33101
date_of_service: 11/15/25
claim_processed_on: 11/22/25
service_count: 3
total_amount_charged: $525.00
total_medicare_approved: $320.00
total_you_may_be_billed: $104.00
complete_claim_json: {"basic_info":{"date_of_service":"11/15/25",...},"services":[{...},{...},{...}],"summary":{...}}
```

### In Excel:

| claim_number | provider | date_of_service | service_count | total_amount_charged | complete_claim_json |
|--------------|----------|-----------------|---------------|----------------------|---------------------|
| 1126005184730 | MARGULIS, MICHAEL E. | 12/30/25 | 2 | $275.00 | {"basic_info":{...},"services":[...],"summary":{...}} |
| 1126005184895 | SMITH, JOHN | 11/15/25 | 3 | $525.00 | {"basic_info":{...},"services":[...],"summary":{...}} |

**Easy to read columns + complete JSON for deep analysis!**

---

## 🎓 Understanding the Data

### Service Breakdown

Each service in the JSON represents one procedure:

```json
{
  "service_name": "EXTENDED EXAM OF THE BACK PART OF THE EYE",
  "procedure_code": "92201",              ← CPT code
  "quantity": "1",                        ← How many times
  "provider_charged": "$75.00",           ← What doctor billed
  "medicare_approved": "$27.44",          ← What Medicare allows
  "applied_to_deductible": "$0.00",       ← Applied to deductible
  "coinsurance": "$5.49",                 ← 20% patient pays
  "you_may_be_billed": "$5.49"            ← Total patient owes
}
```

### Summary Breakdown

The summary totals all services:

```json
"summary": {
  "total_amount_charged": "$275.00",      ← Sum of all provider_charged
  "total_medicare_approved": "$167.33",   ← Sum of all medicare_approved
  "total_coinsurance": "$33.47",          ← Sum of all coinsurance
  "total_you_may_be_billed": "$33.47",    ← Total patient owes
  "total_medicare_paid_provider": "$131.18" ← Medicare paid: approved - coinsurance
}
```

**Formula:** 
```
Provider Charged: $275.00
Medicare Approved: $167.33 (what Medicare thinks is fair)
Medicare Paid: $131.18 (80% of approved)
Patient Owes: $33.47 (20% coinsurance)
```

---

## 🔍 Key Fields Explained

### date_of_service
**When:** The actual date you received medical care  
**Format:** MM/DD/YY  
**Example:** "12/30/25" = December 30, 2025

### claim_processed_on
**When:** When Medicare processed the claim  
**Note:** Usually 1-2 weeks after service date  
**Example:** Service on 12/30, processed on 01/07

### procedure_code (CPT Code)
**What:** Standard medical procedure code  
**Examples:**
- 92201 = Eye exam with retinal drawing
- 92014 = Complete visual system exam
- 99213 = Office visit, established patient
- 93000 = Electrocardiogram (EKG)

### provider_charged vs medicare_approved
**Charged:** What doctor wants to bill you  
**Approved:** What Medicare thinks is reasonable  
**Often different!** Medicare usually pays less than charged

### coinsurance
**What:** Your share of the cost (typically 20%)  
**Calculation:** 20% of Medicare approved amount  
**Example:** $139.89 approved → $27.98 coinsurance

### you_may_be_billed
**What:** Total amount you owe  
**Includes:**
- Deductible (if not met)
- Coinsurance (20%)
- Any non-covered charges

---

## 📋 CSV Output Preview

When you open `detailed_claims_test_output.csv` in Excel:

### Quick-View Columns (for scanning):
```
| claim_number  | provider          | date   | service_count | total_charged | total_billed |
|---------------|-------------------|--------|---------------|---------------|--------------|
| 1126005184730 | MARGULIS, M.      | 12/30  | 2             | $275.00       | $33.47       |
| 1126005184895 | SMITH, J.         | 11/15  | 3             | $525.00       | $104.00      |
| 1126005185123 | JONES, M.         | 10/05  | 1             | $180.00       | $0.00        |
```

### Complete Data Column:
```
| complete_claim_json                                                          |
|------------------------------------------------------------------------------|
| {"basic_info":{"date_of_service":"12/30/25","provider":"MARGULIS, MICHA...  |
| {"basic_info":{"date_of_service":"11/15/25","provider":"SMITH, JOHN","p...  |
| {"basic_info":{"date_of_service":"10/05/25","provider":"JONES, MARY","p...  |
```

**Double-click any JSON cell to see the complete formatted data!**

---

## 🎨 Visualizing the Structure

### Hierarchical View:

```
Claim
├── basic_info (6 fields)
│   ├── date_of_service
│   ├── provider
│   ├── provider_address
│   ├── claim_processed_on
│   ├── practicing_providers
│   └── claim_number
│
├── services (array of service objects)
│   ├── Service 1
│   │   ├── service_name
│   │   ├── procedure_code
│   │   ├── quantity
│   │   ├── provider_charged
│   │   ├── medicare_approved
│   │   ├── applied_to_deductible
│   │   ├── coinsurance
│   │   └── you_may_be_billed
│   │
│   ├── Service 2
│   │   └── (same fields as Service 1)
│   │
│   └── Service N...
│
├── summary (12 financial totals)
│   ├── total_amount_charged
│   ├── total_medicare_approved
│   ├── blood_deductible
│   ├── physical_therapy_charges
│   ├── psychiatric_charges
│   ├── occupational_therapy_charges
│   ├── total_patient_paid_provider
│   ├── total_medicare_paid_you
│   ├── total_medicare_paid_provider
│   ├── total_applied_to_deductible
│   ├── total_coinsurance
│   └── total_you_may_be_billed
│
└── validation_info (2 fields)
    ├── provider_from_card
    └── date_from_card
```

---

## 🔧 Parsing Examples

### Python: Get All Procedure Codes

```python
import json
import pandas as pd

df = pd.read_csv('detailed_claims_test_output.csv')

for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    provider = claim['basic_info']['provider']
    codes = [s['procedure_code'] for s in claim['services']]
    print(f"{provider}: {', '.join(codes)}")
```

**Output:**
```
MARGULIS, MICHAEL E.: 92201, 92014
SMITH, JOHN: 99213, 93000, 93015
JONES, MARY: G0438
```

### Python: Calculate Total Owed Across All Claims

```python
total_owed = 0
for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    amount_str = claim['summary']['total_you_may_be_billed']
    amount = float(amount_str.replace('$', '').replace(',', ''))
    total_owed += amount

print(f"Total patient owes across all claims: ${total_owed:.2f}")
```

### Python: Find High-Cost Services

```python
high_cost_services = []

for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    provider = claim['basic_info']['provider']
    
    for service in claim['services']:
        charged = float(service['provider_charged'].replace('$', '').replace(',', ''))
        if charged > 200:
            high_cost_services.append({
                'provider': provider,
                'service': service['service_name'],
                'code': service['procedure_code'],
                'charged': charged
            })

for item in high_cost_services:
    print(f"{item['provider']}: {item['service']} (${item['charged']})")
```

---

## 📊 Data Analysis Examples

### 1. Services Frequency

```python
from collections import Counter

all_procedures = []
for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    for service in claim['services']:
        all_procedures.append(service['procedure_code'])

counts = Counter(all_procedures)
print("Most common procedures:")
for code, count in counts.most_common(5):
    print(f"  {code}: {count} times")
```

### 2. Provider Comparison

```python
providers_summary = {}

for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    provider = claim['basic_info']['provider']
    charged = claim['summary']['total_amount_charged']
    billed = claim['summary']['total_you_may_be_billed']
    
    if provider not in providers_summary:
        providers_summary[provider] = {'charged': [], 'billed': []}
    
    providers_summary[provider]['charged'].append(charged)
    providers_summary[provider]['billed'].append(billed)

# Show which providers cost most
for provider, amounts in providers_summary.items():
    print(f"{provider}: Avg charged: {sum(amounts['charged'])/len(amounts['charged'])}")
```

### 3. Export to Separate Files

```python
# Save each claim as individual JSON file
for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    provider = claim['basic_info']['provider'].replace(',', '').replace(' ', '_')
    date = claim['basic_info']['date_of_service'].replace('/', '-')
    
    filename = f"claim_{provider}_{date}.json"
    with open(filename, 'w') as f:
        json.dump(claim, f, indent=2)
```

---

## 🎯 Complete Example Output

### If you extract 5 claims, you get:

**detailed_claims_test_output.csv** with 5 rows:

```csv
claim_number,provider,provider_address,date_of_service,claim_processed_on,service_count,total_amount_charged,total_medicare_approved,total_you_may_be_billed,complete_claim_json
1126005184730,MARGULIS MICHAEL E.,"123 GROVE AVE, STE 214, CEDARHURST, NY 11516-2302",12/30/25,01/07/26,2,$275.00,$167.33,$33.47,"{""basic_info"":{""date_of_service"":""12/30/25"",""provider"":""MARGULIS, MICHAEL E."",""provider_address"":""123 GROVE AVE, STE 214, CEDARHURST, NY 11516-2302"",""claim_processed_on"":""01/07/26"",""practicing_providers"":""Not available"",""claim_number"":""1126005184730""},""services"":[{""service_name"":""EXTENDED EXAM OF THE BACK PART OF THE EYE WITH RETINAL DRAWING"",""procedure_code"":""92201"",""quantity"":""1"",""provider_charged"":""$75.00"",""medicare_approved"":""$27.44"",""applied_to_deductible"":""$0.00"",""coinsurance"":""$5.49"",""you_may_be_billed"":""$5.49""},{""service_name"":""ESTABLISHED PATIENT COMPLETE EXAM OF VISUAL SYSTEM"",""procedure_code"":""92014"",""quantity"":""1"",""provider_charged"":""$200.00"",""medicare_approved"":""$139.89"",""applied_to_deductible"":""$0.00"",""coinsurance"":""$27.98"",""you_may_be_billed"":""$27.98""}],""summary"":{""total_amount_charged"":""$275.00"",""total_medicare_approved"":""$167.33"",""blood_deductible"":""$0.00"",""physical_therapy_charges"":""$0.00"",""psychiatric_charges"":""$0.00"",""occupational_therapy_charges"":""$0.00"",""total_patient_paid_provider"":""$0.00"",""total_medicare_paid_you"":""$0.00"",""total_medicare_paid_provider"":""$131.18"",""total_applied_to_deductible"":""$0.00"",""total_coinsurance"":""$33.47"",""total_you_may_be_billed"":""$33.47""}}"
... (4 more rows)
```

---

## 💡 Pro Tips

### 1. Pretty-Print JSON for Reading

```python
import json

json_str = df.iloc[0]['complete_claim_json']
claim = json.loads(json_str)
print(json.dumps(claim, indent=2))
```

### 2. Extract to Separate Sheets

```python
import pandas as pd
import json

df = pd.read_csv('detailed_claims_test_output.csv')

# Create Excel with multiple sheets
with pd.ExcelWriter('claims_detailed.xlsx') as writer:
    # Sheet 1: Summary
    df[['claim_number', 'provider', 'date_of_service', 'total_amount_charged']].to_excel(
        writer, sheet_name='Summary', index=False
    )
    
    # Sheet 2: All services from all claims
    all_services = []
    for idx, row in df.iterrows():
        claim = json.loads(row['complete_claim_json'])
        for service in claim['services']:
            service['provider'] = claim['basic_info']['provider']
            service['date'] = claim['basic_info']['date_of_service']
            all_services.append(service)
    
    pd.DataFrame(all_services).to_excel(writer, sheet_name='Services', index=False)
```

### 3. Filter by Procedure Type

```python
# Find all eye exam claims:
eye_exam_codes = ['92201', '92014', '92004', '92012']

for idx, row in df.iterrows():
    claim = json.loads(row['complete_claim_json'])
    has_eye_exam = any(
        s['procedure_code'] in eye_exam_codes 
        for s in claim['services']
    )
    if has_eye_exam:
        print(f"Eye exam: {claim['basic_info']['provider']}")
```

---

## ✅ Summary

**What you get:**
- ✅ Complete claim data (25+ fields per claim)
- ✅ All services with procedure codes
- ✅ All financial amounts
- ✅ JSON format for easy parsing
- ✅ CSV format for easy viewing
- ✅ Only valid doctors (filtered automatically)

**Perfect for:**
- Testing extraction before bulk run
- Analyzing specific accounts
- Getting detailed billing information
- Building custom reports
- Auditing claims data

**Run the test script and you'll have complete claim details in minutes!** 🚀
