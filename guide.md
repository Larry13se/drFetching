# Medicare Processor - Complete Usage Guide

## 🚀 Quick Start

### **Option 1: Using Launcher (Recommended for Beginners)**
```bash
python medicare_launcher.py
```
This will show you an interactive menu where you can choose:
- Multi-threaded with different thread counts (2, 3, 5, or custom)
- Single-threaded mode
- Easy selection without remembering commands

### **Option 2: Using Environment Variables (Direct)**

#### Windows PowerShell:
```powershell
# Multi-threaded (5 threads)
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="5"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Multi-threaded (3 threads)
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="3"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Single-threaded
$env:THREADING_MODE="single"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s
```

#### Windows CMD:
```cmd
# Multi-threaded (5 threads)
set THREADING_MODE=multi
set THREAD_COUNT=5
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Single-threaded
set THREADING_MODE=single
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s
```

#### Linux/Mac:
```bash
# Multi-threaded (5 threads)
export THREADING_MODE=multi
export THREAD_COUNT=5
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Single-threaded
export THREADING_MODE=single
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s
```

### **Option 3: Using Batch/Shell Scripts**

Create these files in your project directory:

**Windows - `run_multi_5.bat`:**
```batch
@echo off
set THREADING_MODE=multi
set THREAD_COUNT=5
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s
pause
```

**Linux/Mac - `run_multi_5.sh`:**
```bash
#!/bin/bash
export THREADING_MODE=multi
export THREAD_COUNT=5
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s
```

Then run:
```bash
# Windows
run_multi_5.bat

# Linux/Mac (make executable first)
chmod +x run_multi_5.sh
./run_multi_5.sh
```

---

## 📋 Configuration Options

### Thread Count Recommendations

| Threads | Use Case | Speed | Detection Risk |
|---------|----------|-------|----------------|
| 1 (Single) | Testing, problematic accounts | Slowest | Lowest |
| 2 | Conservative production | Slow | Very Low |
| 3 | Balanced production | Moderate | Low |
| 5 | **Recommended production** | Fast | Moderate |
| 8 | Aggressive (not recommended) | Fastest | High |

### Browser Options
```bash
--browser=chrome   # Default
--browser=edge     # Microsoft Edge
--browser=firefox  # Firefox
```

---

## 🎯 Common Usage Scenarios

### **Scenario 1: First Time Running**
Start conservative to test your system:
```bash
python medicare_launcher.py
# Select option 3 (2 threads)
```

### **Scenario 2: Production Run**
Once tested, use 5 threads for optimal speed:
```bash
# Windows PowerShell
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="5"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Or use launcher
python medicare_launcher.py
# Select option 1 (5 threads)
```

### **Scenario 3: Troubleshooting Failures**
If you're getting many failures, reduce to single-threaded:
```bash
# Windows PowerShell
$env:THREADING_MODE="single"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Or use launcher
python medicare_launcher.py
# Select option 5 (Single-threaded)
```

### **Scenario 4: Different Browser**
```bash
# Windows PowerShell with Edge
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="3"
python -m pytest integrated_medicare_processor.py --browser=edge -v -s
```

---

## 📊 Monitoring Progress

### Real-time Monitoring

**Option 1: Watch the log file**
```bash
# Windows PowerShell
Get-Content medicare_processor.log -Wait -Tail 20

# Linux/Mac
tail -f medicare_processor.log
```

**Option 2: Check console output**
The `-s` flag in pytest shows all print statements in real-time.

### Progress Tracking Commands

**Count completed accounts:**
```bash
# Windows PowerShell
(Select-String -Path medicare_processor.log -Pattern "Thread completed successfully").Count

# Linux/Mac
grep -c "Thread completed successfully" medicare_processor.log
```

**Check for errors:**
```bash
# Windows PowerShell
Select-String -Path medicare_processor.log -Pattern "ERROR"

# Linux/Mac
grep "ERROR" medicare_processor.log
```

**See active threads:**
```bash
# Windows PowerShell
Select-String -Path medicare_processor.log -Pattern "Starting thread" | Select-Object -Last 5

# Linux/Mac
grep "Starting thread" medicare_processor.log | tail -5
```

---

## 🛠️ Troubleshooting

### Issue 1: "unrecognized arguments" Error

**Problem:**
```
error: unrecognized arguments: --threads=5
```

**Solution:**
Don't use `--threads` flag. Use environment variables instead:
```bash
# Windows
set THREADING_MODE=multi
set THREAD_COUNT=5

# Linux/Mac
export THREADING_MODE=multi
export THREAD_COUNT=5
```

### Issue 2: High Failure Rate

**Solution:**
```bash
# Reduce thread count
$env:THREAD_COUNT="2"  # Windows
export THREAD_COUNT=2   # Linux/Mac

# Or use single-threaded
$env:THREADING_MODE="single"
```

### Issue 3: Browser Not Starting

**Solution:**
1. Check browser is installed
2. Update SeleniumBase: `pip install --upgrade seleniumbase`
3. Try different browser: `--browser=edge` or `--browser=firefox`

### Issue 4: CSV File Corruption

**Solution:**
The ThreadSafeCSVWriter should prevent this. If it happens:
1. Check `medicare_processor.log` for errors
2. Look for backup files: `medicare_results_taxonomy.csv.backup_*`
3. Ensure sufficient disk space

### Issue 5: Memory Issues

**Solution:**
```bash
# Reduce thread count
$env:THREAD_COUNT="2"

# Each thread uses ~500MB RAM
# 5 threads = ~2.5GB RAM needed
```

---

## 📈 Performance Optimization

### For Speed (if system can handle it)
```bash
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="5"
$env:THREAD_STARTUP_DELAY="1"  # Optional: faster startup
```

### For Reliability (recommended for production)
```bash
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="3"
# Use default delays
```

### For Stealth (avoid detection)
```bash
$env:THREADING_MODE="multi"
$env:THREAD_COUNT="2"
# Built-in delays are already optimized
```

---

## 📁 Output Files

### `medicare_results_taxonomy.csv`
- Main results file
- Contains all processed accounts
- Thread-safe (no corruption from concurrent writes)

### `medicare_processor.log`
- Detailed execution log
- Thread-specific entries
- Error tracking
- Useful for debugging

### Backup Files
- Format: `medicare_results_taxonomy.csv.backup_<timestamp>`
- Automatically created if file corruption detected

---

## 🔄 Stopping and Resuming

### Graceful Stop
Press `Ctrl+C` once and wait for threads to finish current accounts.

### Force Stop
Press `Ctrl+C` twice for immediate termination (may lose data for accounts currently processing).

### Resuming
The processor does NOT automatically resume. To continue:
1. Check `medicare_results_taxonomy.csv` for completed accounts
2. Remove completed accounts from input CSV
3. Re-run the processor

---

## ⚙️ Advanced Configuration

### Custom Configuration
Edit these variables in `integrated_medicare_processor.py`:

```python
# Thread settings
MAX_CONCURRENT_THREADS = 5  # Default thread count
THREAD_STARTUP_DELAY = 2    # Seconds between thread starts

# Timing delays
TYPING_DELAY = (0.02, 0.06)  # Character typing speed
CLICK_DELAY = (0.01, 0.04)   # Click delays
PAGE_SETTLE = (0.8, 1.5)     # Page loading waits
LOGIN_TIMEOUT = 25           # Login wait time
```

### Environment Variables Available
```bash
THREADING_MODE   # 'single' or 'multi'
THREAD_COUNT     # Number of concurrent threads (1-10)
```

---

## 📞 Quick Reference

### Start Multi-threaded (5 threads) - RECOMMENDED
```bash
# Windows PowerShell
$env:THREADING_MODE="multi"; $env:THREAD_COUNT="5"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Or simply
python medicare_launcher.py
# Then select option 1
```

### Start Single-threaded
```bash
# Windows PowerShell
$env:THREADING_MODE="single"
python -m pytest integrated_medicare_processor.py --browser=chrome -v -s

# Or
python medicare_launcher.py
# Then select option 5
```

### Monitor Progress
```bash
# Windows PowerShell
Get-Content medicare_processor.log -Wait -Tail 20

# Check completion count
(Select-String -Path medicare_processor.log -Pattern "completed successfully").Count
```

---

## ✅ Best Practices

1. **Always start with 2-3 threads** for first run
2. **Monitor logs** for first 10-15 minutes
3. **Increase threads gradually** if stable
4. **Use launcher for simplicity**: `python medicare_launcher.py`
5. **Check CSV output** periodically for data quality
6. **Keep backup** of input CSV file
7. **Don't exceed 8 threads** (high detection risk)

---

## 🎓 Examples

### Example 1: Test Run (2 accounts)
1. Create a test CSV with 2 accounts
2. Run single-threaded first
3. Verify results in output CSV

### Example 2: Production Run (322 accounts)
1. Start with 3 threads
2. Monitor for 30 minutes
3. If stable, restart with 5 threads
4. Check results periodically

### Example 3: Retry Failed Accounts
1. Filter failed accounts from results CSV
2. Create new input CSV with failed accounts
3. Run with single-threaded mode
4. Investigate specific errors in log file

---

## 🆘 Getting Help

If you encounter issues:
1. Check `medicare_processor.log` for detailed errors
2. Try single-threaded mode for debugging
3. Reduce thread count if getting rate-limited
4. Verify input CSV format matches expected structure
5. Ensure all dependencies are installed: `pip install -r requirements.txt`