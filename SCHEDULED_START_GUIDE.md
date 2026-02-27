# Scheduled Start Feature Guide

## Overview

The Medicare processor now supports **scheduled/delayed start**, allowing you to start the script now but have it wait before actually processing leads.

---

## How to Use

### 1. Set Your Delay

Edit `integrated_medicare_processor.py` at the top:

```python
# SCHEDULED START - Set hours to delay before starting (0 = start immediately)
DELAY_START_HOURS = 3      # Wait 3 hours before starting
DELAY_START_MINUTES = 0    # Additional minutes (optional)
```

### 2. Run the Script

```bash
python integrated_medicare_processor.py
```

### 3. What You'll See

```
==========================================
MEDICARE CLAIMS PROCESSOR - FAST & RELIABLE
==========================================
Input file: Submission Data - EXPORT (2).csv
Output file: medicare_results_FINAL.csv
Threads: 6
Browser distribution: {'chrome': 6}
Retry: Up to 3 retries for errors
==========================================

⏰ SCHEDULED START
==========================================
Current time:    2026-01-30 02:30:15 PM
Scheduled start: 2026-01-30 05:30:15 PM
Delay: 3 hours and 0 minutes
==========================================

💤 Waiting for scheduled time...
(Press Ctrl+C to cancel and exit)

⏳ Time remaining: 02:59:45
```

The countdown updates every second showing hours:minutes:seconds remaining.

### 4. When Time is Reached

```
✅ Scheduled time reached! Starting processing...

Found 150 accounts to process
...
```

The script will automatically start processing your leads.

---

## Common Use Cases

### Start Immediately (Default)
```python
DELAY_START_HOURS = 0
DELAY_START_MINUTES = 0
```

### Wait 1 Hour
```python
DELAY_START_HOURS = 1
DELAY_START_MINUTES = 0
```

### Wait 3 Hours (Your Setting)
```python
DELAY_START_HOURS = 3
DELAY_START_MINUTES = 0
```

### Wait 2 Hours 30 Minutes
```python
DELAY_START_HOURS = 2
DELAY_START_MINUTES = 30
```

### Wait 30 Minutes
```python
DELAY_START_HOURS = 0
DELAY_START_MINUTES = 30
```

### Wait Until Overnight (8 Hours)
```python
DELAY_START_HOURS = 8
DELAY_START_MINUTES = 0
```

---

## Canceling the Wait

If you change your mind during the countdown:

1. **Press Ctrl+C** in the terminal
2. The script will display:
   ```
   ❌ Scheduled start cancelled by user. Exiting...
   ```
3. The script will exit cleanly without processing any leads

---

## Tips

### 1. Planning Overnight Runs
If you want to start processing at midnight:
- Check current time: 4:00 PM
- Calculate delay: 8 hours until midnight
- Set: `DELAY_START_HOURS = 8`

### 2. Running During Off-Peak Hours
Medicare.gov might be less busy at night:
- Set delay to start at 11 PM or 2 AM
- Less traffic = potentially faster processing

### 3. Avoiding Detection
Adding random start times can help:
- Day 1: Start at 2 PM (no delay)
- Day 2: Start at 5 PM (3 hour delay)
- Day 3: Start at 8 PM (6 hour delay)

### 4. Testing First
Before a long delay:
1. Set `DELAY_START_HOURS = 0` and `DELAY_START_MINUTES = 2`
2. Test that everything works with a 2-minute delay
3. Then set your real delay (3 hours)

---

## Visual Timeline Example

### Current Setup (3 hours)

```
You run script → 2:00 PM
                  ↓
                [Waiting... countdown shows remaining time]
                  ↓
                  ↓ 3 hours pass
                  ↓
Script starts  → 5:00 PM
                  ↓
                [Processing 150 leads... ~2-3 hours]
                  ↓
Complete       → 7:00-8:00 PM
```

---

## Technical Details

### How It Works
1. Script starts immediately but pauses execution
2. Shows real-time countdown (updates every second)
3. Calculates exact start time based on current time + delay
4. When countdown reaches 0:00:00, processing begins
5. If Ctrl+C pressed during wait, exits cleanly

### What Happens During Wait
- ✅ Script is running (you'll see it in task manager)
- ✅ Countdown updates every second
- ✅ Can be cancelled with Ctrl+C
- ❌ No browser windows open yet
- ❌ No leads processed yet
- ❌ No network activity

### Computer Requirements
- Computer must stay on during wait period
- Script window must remain open
- Don't put computer to sleep
- Internet connection not needed during wait (only when processing starts)

---

## Troubleshooting

### Script Exits Immediately
**Problem:** Set `DELAY_START_HOURS = 0` and `DELAY_START_MINUTES = 0`
**Solution:** This means "start now" - increase hours/minutes if you want a delay

### Countdown Not Showing
**Problem:** Terminal might not support \r (carriage return)
**Solution:** Countdown still works, just might not update smoothly on screen

### Computer Goes to Sleep
**Problem:** Computer sleep/hibernate during wait period
**Solution:**
- Disable sleep mode in Windows power settings
- Or use a shorter delay and start script closer to when you want it to run

### Want to Change Delay After Starting
**Problem:** Script already waiting, want different time
**Solution:**
1. Press Ctrl+C to cancel
2. Change `DELAY_START_HOURS` value
3. Run script again

---

## Example Scenarios

### Scenario 1: Night Owl Processing
"I want to start processing at 11 PM so it runs overnight"

Current time: 8:00 PM
Desired start: 11:00 PM
Delay needed: 3 hours

```python
DELAY_START_HOURS = 3
DELAY_START_MINUTES = 0
```

### Scenario 2: Lunch Break Start
"I want to go to lunch and have it start when I get back"

Current time: 12:00 PM
Desired start: 1:30 PM
Delay needed: 1.5 hours

```python
DELAY_START_HOURS = 1
DELAY_START_MINUTES = 30
```

### Scenario 3: After Work Processing
"I'm at work, want to start it when I get home"

Current time: 9:00 AM
Desired start: 6:00 PM
Delay needed: 9 hours

```python
DELAY_START_HOURS = 9
DELAY_START_MINUTES = 0
```

---

## FAQ

**Q: Can I close the terminal window during the wait?**
A: No, closing the terminal will exit the script. Keep it open.

**Q: What if my computer crashes during the wait?**
A: Script will exit. You'll need to restart it.

**Q: Can I change the delay while it's counting down?**
A: No, press Ctrl+C to cancel, change config, and restart.

**Q: Does the wait use a lot of computer resources?**
A: No, it's just a sleep loop. Very minimal CPU/memory usage.

**Q: Will it start exactly at the scheduled time?**
A: Yes, accurate to the second (unless system is under heavy load).

**Q: Can I schedule multiple runs?**
A: Not automatically. You'd need to restart the script each time.

---

## Quick Reference

| Want to Start | Current Time | Set Hours To |
|---------------|--------------|--------------|
| Immediately | Any | 0 |
| In 30 min | Any | 0 (set minutes to 30) |
| In 1 hour | Any | 1 |
| In 3 hours | Any | 3 |
| At midnight | 4:00 PM | 8 |
| At 6:00 AM | 10:00 PM | 8 |
| Next day noon | 10:00 AM | 26 |

---

**Your current setting: Wait 3 hours before starting** ⏰
