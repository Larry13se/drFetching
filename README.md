# Medicare Claims Processor – Architecture & Runbook

This document explains how the automation works end-to-end: the main flow, how modules interact, which CSVs are used, and how to run and troubleshoot it.

## What the App Does
Automates Medicare.gov account logins, scrapes recent claims, validates doctors against CMS NPI/PECOS data plus taxonomy rules, and writes filtered provider results per account to CSV (one output file per worker thread).

## Core Files & Responsibilities
- `integrated_medicare_processor.py` — Main orchestrator. Handles threading, browser automation (SeleniumBase), login, claims scraping, doctor evaluation, and CSV output.
- `DR_eval.py` — Services for external/auxiliary data:
  - `NPIRegistryService` (CMS NPI API + PECOS JSON fallback)
  - `PECOSEnrollmentService` (CMS PECOS enrollment API)
  - `TaxonomyBasedSpecialtyValidator` (uses `taxonomy.csv` + `bad specs.csv`)
- `improved_captcha_handler.py` — Robust CAPTCHA detection/solving used by the processor.
- `config.py` — Legacy/alternate config constants (paths, timing, output columns). The threaded processor currently uses its own constants at the top of `integrated_medicare_processor.py`.
- `cleaning_script.py` — Standalone notebook-style utility to combine and analyze CSVs (not part of the run flow).
- `filter_pure_resault.ipynb` — Notebook for data filtering/analysis (not part of the run flow).
- `taxonomy.csv` — Reference taxonomy codes with GOOD/BAD categories.
- `bad specs.csv` — CN-eligible specialty keywords (for “good for CN” classification).
- `pecos_data.json` — Local PECOS dataset fallback for provider lookups.

## Inputs & Outputs (CSVs/JSON)
- **Credentials/input CSV** (`CREDENTIALS_FILE` in `integrated_medicare_processor.py`, default: `Submission Data - 12-01-2025 - 323 Pure Leads.csv`)
  - Must include at least `username` and `password` columns.
  - Additional patient fields (e.g., `PT State`, `DR1`… if present) are passed through to output rows and used for state context.
- **Taxonomy reference**: `taxonomy.csv` (GOOD/BAD per taxonomy code).
- **Bad specialty keywords**: `bad specs.csv` (CN-eligible specialty keywords).
- **PECOS dataset**: `pecos_data.json` (used when CMS NPI API returns nothing or errors).
- **Outputs**: `medicare_results_taxonomy_thread_<thread_id>.csv`
  - Contains session fingerprinting columns, DR slots (DR1…DR20 with address/date/NPI/enrollment/specialty/source), counts, and categorized suggestion columns (bad specialty / not found / not enrolled / other).
  - One file per worker thread.
- **Logs/artifacts** (when errors occur):
  - Debug HTML files like `debug_page_source_<timestamp>.html`
  - Optional screenshots (commented in CAPTCHA handler)

## High-Level Flow
1. **Load credentials**  
   - `load_credentials()` reads `CREDENTIALS_FILE` and gathers `(username, password, row_data)` tuples.
2. **Batch & thread setup**  
   - `split_list()` divides accounts across threads based on `NUM_THREADS` and `BROWSER_DISTRIBUTION` (e.g., 6 Chrome instances).
   - `worker_thread()` creates a `ThreadedMedicareProcessor` (inherits `BaseCase`) per thread, keeps browser open, and processes its batch sequentially.
3. **Per-account processing** (`process_account_with_retry` → `process_account`)
   - Collect session fingerprint (user agent, screen size, timezone, hash).
   - Login (`attempt_login`) with hardened input methods, retryable errors, CAPTCHA checks, and 2FA detection.
   - Navigate to Claims (`navigate_to_claims`).
   - Collect claims list (`get_all_claim_cards_basic_info`):
     - Stops once claims are older than 9 months (`subtract_months(date.today(), 9)`).
     - Skips companies via `is_company`.
     - Records card index and date for later deep extraction.
   - Evaluate providers (`process_claims_with_taxonomy_evaluation`):
     - Fast path: evaluate provider name/state directly via `evaluate_doctor_by_name_and_state`.
     - If missing info, open claim details (`click_claim_details`), extract provider + address (`extract_provider_details`), re-evaluate (including cross-state if address implies a different state).
     - Uses `NPIRegistryService` + `TaxonomyBasedSpecialtyValidator` + `PECOSEnrollmentService` to classify:
       - `GOOD` (kept)
       - `CN_ELIGIBLE` (kept, marked CN)
       - `BAD_SPECIALTY`, `NOT_FOUND`, `NOT_ENROLLED`, or other failure (saved as suggestions)
   - Write results (`write_result`):
     - On success: writes good and CN providers into DR slots, suggestions into categorized columns, session fingerprint data, and counts.
     - On failure: writes error reason (e.g., `LOGIN_FAILED:...`, `NAVIGATION_FAILED`, `CAPTCHA_FAILED`, `NO VALID Doctors-old/companies/bad`).
   - Logout best-effort.
4. **Thread lifecycle & resilience**
   - Retryable errors (see `RETRYABLE_ERROR_TYPES`) get up to `MAX_RETRYABLE_ERRORS` attempts with delays.
   - Consecutive failures trigger `emergency_reset` (clears cookies, reloads login).
   - `success_counter` / `failure_counter` track totals across threads.
5. **Finish**
   - Main entry `test_run_threaded_batch_processing()` starts threads, joins them, and prints totals and output file pattern.

## Module Interactions
- `ThreadedMedicareProcessor`
  - Uses `ImprovedCaptchaHandler` for CAPTCHA detection/solving at multiple checkpoints.
  - Uses `NPIRegistryService` (CMS NPI API) with `TaxonomyBasedSpecialtyValidator` (taxonomy/bad specs files) and `PECOSEnrollmentService` (CMS PECOS API) to classify providers.
  - Writes CSV output directly (thread-specific files); uses thread-safe locks for file writes where needed.
- `DR_eval.py`
  - Provides provider lookup, enrollment check, and taxonomy-based classification.
  - Falls back to local `pecos_data.json` when APIs fail or return nothing.
- `improved_captcha_handler.py`
  - Called during login and other navigation points to monitor/solve CAPTCHAs robustly (iframe-aware, multi-attempt).

## Key Config Knobs (threaded processor)
- File names: `CREDENTIALS_FILE`, `OUTPUT_FILE_PREFIX`
- Threading: `NUM_THREADS`, `BROWSER_DISTRIBUTION`
- Timing: `TYPING_DELAY`, `CLICK_DELAY`, `PAGE_SETTLE`, `CAPTCHA_WAIT`, `LOGIN_TIMEOUT`, `CLAIMS_LOAD_TIMEOUT`, `DETAIL_TIMEOUT`, `NAVIGATION_TIMEOUT`
- Retry: `MAX_RETRYABLE_ERRORS`, `RETRYABLE_ERROR_TYPES`
- Anti-bot: randomized delays, mouse movements, stealth JS injection
- Claim age cutoff: 9 months back (`subtract_months`)

> Note: `config.py` holds similar knobs for an older/alternate flow; the current threaded runner uses the constants at the top of `integrated_medicare_processor.py`.

## Running the App (typical)
From project root (ensure dependencies installed, e.g., `pip install -r requirements.txt`):
```bash
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s
```
Environment variables (optional) for threading can mirror those in `guide.md`, but the threaded constants inside the file control defaults (NUM_THREADS, BROWSER_DISTRIBUTION, etc.).

## Data Columns (outputs)
- Session/fingerprint: fingerprint hash, timestamp, user agent, screen resolution, timezone, session duration, browser language.
- Counts: `DR_COUNT`, `DR_SUGGESTIONS_COUNT`.
- DR slots: `DR1`…`DR20` each with `_ADDRESS`, `_DATE`, `_NPI`, `_ENROLLMENT`, `_SPECIALTY`, `_SOURCE`.
- Suggestions: `DR_SUGGESTION_BAD_SPECIALTY`, `DR_SUGGESTION_NOT_FOUND`, `DR_SUGGESTION_NOT_ENROLLED`, `DR_SUGGESTION_OTHER`.

## Error Handling & Resilience
- Login error detection via text patterns (`ERROR_PATTERNS`), rate-limit detection, and 2FA detection.
- CAPTCHA: monitored and solved at multiple steps; retries and refresh on failure.
- Navigation: refresh strategies, safe page operations, and emergency reset after consecutive failures.
- Retryable vs. non-retryable errors gate whether an account is retried.

## File/Directory Map (relevant)
- Root:
  - `integrated_medicare_processor.py`
  - `DR_eval.py`
  - `improved_captcha_handler.py`
  - `config.py`
  - `cleaning_script.py`
  - `filter_pure_resault.ipynb`
  - Data: `taxonomy.csv`, `bad specs.csv`, `pecos_data.json`, input credential CSV(s), output CSVs (`medicare_results_taxonomy_thread_<id>.csv`)

## Operational Notes
- Keep input CSV clean: ensure `username`/`password` and state columns are present and correctly spelled.
- Verify `taxonomy.csv` and `bad specs.csv` exist; otherwise the validator will create a sample taxonomy file or log missing data.
- Network/API dependency: CMS NPI and PECOS APIs are used; failures fall back to local PECOS JSON.
- Browser: SeleniumBase-powered; Chrome is default (`BROWSER_DISTRIBUTION`), but Edge/Firefox are supported if wired into distribution.
- Stopping safely: Ctrl+C once lets threads finish current work; twice forces termination (may lose in-flight account results).

## Troubleshooting Checklist
- Login fails quickly → check credentials CSV and site availability; watch for 2FA-required accounts.
- Frequent CAPTCHA → ensure CAPTCHA handler files are present; allow time for solve attempts; consider lowering thread count.
- Empty outputs → claims older than 9 months, providers filtered as companies, or taxonomy/bad-spec rules excluded them.
- “Not enrolled” outcomes → PECOS enrollment check may be returning false; verify with provider NPI manually if needed.
- Rate limiting/system errors → reduce `NUM_THREADS`, increase delays, or pause between batches.

# drFetching
# drFetching
