import os
import random
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

import dearpygui.dearpygui as dpg

try:
    from hss_switcher import connect_location, LOCATIONS as HSS_LOCATIONS
except Exception:
    connect_location = None
    HSS_LOCATIONS = []

ROOT = Path(__file__).resolve().parent
PROCESS_NAMES = ["node", "python"]

SUSPENDED = set()
handler_thread: threading.Thread | None = None
handler_stop_event = threading.Event()

# Timing
HSS_INTERVAL_SEC = 240  # 4 minutes between switches
HSS_POST_DELAY_SEC = 10  # 10 seconds wait before resume

# UI state
status_label_id = None
handler_label_id = None
step_label_id = None
timer_label_id = None
log_widget_id = None
log_lines = deque(maxlen=500)
ui_updates = deque()


def _run_powershell(cmd: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        cwd=ROOT,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _get_pids_by_name(names) -> set[int]:
    pids: set[int] = set()
    for name in names:
        cmd = (
            f"Get-Process {name} -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty Id"
        )
        code, out, _ = _run_powershell(cmd)
        if code == 0 and out:
            pids.update(int(line) for line in out.splitlines() if line.strip().isdigit())
    return pids


def _suspend_or_resume(pids: set[int], action: str):
    if not pids:
        return
    if action not in {"suspend", "resume"}:
        raise ValueError("action must be 'suspend' or 'resume'")

    pid_list = ",".join(str(p) for p in pids)
    ps_script = rf'''
$signature = @"
using System;
using System.Runtime.InteropServices;
public static class ProcessExtensions {{
    [DllImport("ntdll.dll", SetLastError=true)]
    public static extern int NtSuspendProcess(IntPtr handle);
    [DllImport("ntdll.dll", SetLastError=true)]
    public static extern int NtResumeProcess(IntPtr handle);
    public static void Suspend(int pid) {{
        var proc = System.Diagnostics.Process.GetProcessById(pid);
        NtSuspendProcess(proc.Handle);
    }}
    public static void Resume(int pid) {{
        var proc = System.Diagnostics.Process.GetProcessById(pid);
        NtResumeProcess(proc.Handle);
    }}
}}
"@
Add-Type -TypeDefinition $signature -ErrorAction SilentlyContinue
$procIds = "{pid_list}".Split(",") | ForEach-Object {{ [int]$_ }}
foreach ($procId in $procIds) {{
    try {{
        if ("{action}" -eq "suspend") {{
            [ProcessExtensions]::Suspend($procId)
        }} else {{
            [ProcessExtensions]::Resume($procId)
        }}
    }} catch {{}}
}}
'''
    code, out, err = _run_powershell(ps_script)
    if code != 0:
        raise RuntimeError(err or out or "Suspend/Resume failed")


def _collect_target_pids() -> set[int]:
    pids = _get_pids_by_name(PROCESS_NAMES)
    pids.discard(os.getpid())
    return pids


def _enqueue_log(message: str):
    timestamp = time.strftime("%H:%M:%S")
    log_lines.append(f"[{timestamp}] {message}")
    ui_updates.append(("log", "\n".join(log_lines)))


def _enqueue_status(target_id, value: str):
    ui_updates.append(("set_value", target_id, value))


def _enqueue_step(step_text: str):
    ui_updates.append(("set_value", step_label_id, step_text))


def _enqueue_timer(timer_text: str):
    ui_updates.append(("set_value", timer_label_id, timer_text))


def _countdown_sleep(total_seconds: int, step_text: str):
    for remaining in range(total_seconds, -1, -1):
        if handler_stop_event.is_set():
            break
        _enqueue_step(step_text)
        _enqueue_timer(f"[TIMER] Time remaining: {remaining}s")
        time.sleep(1)
    _enqueue_timer("")


def _flush_ui():
    while ui_updates:
        kind, *rest = ui_updates.popleft()
        if kind == "set_value":
            target, value = rest
            try:
                dpg.set_value(target, value)
            except Exception:
                pass
        elif kind == "log":
            (text,) = rest
            try:
                dpg.set_value(log_widget_id, text)
            except Exception:
                pass


def _pause():
    _enqueue_status(status_label_id, "Status: Pausing processes...")
    _enqueue_step("[SEARCH] Finding target processes...")
    _enqueue_timer("")
    pids = _collect_target_pids()
    if not pids:
        _enqueue_status(status_label_id, "Status: No target processes found.")
        _enqueue_step("[FAIL] No processes found")
        _enqueue_log("No target node/python processes found.")
        return
    _enqueue_step(f"[PAUSE] Suspending {len(pids)} process(es)...")
    _suspend_or_resume(pids, action="suspend")
    SUSPENDED.update(pids)
    _enqueue_status(status_label_id, f"Status: [OK] Paused {len(pids)} process(es).")
    _enqueue_step(f"[OK] Paused {len(pids)} process(es)")
    _enqueue_log(f"Suspended PIDs: {', '.join(map(str, sorted(pids)))}")


def _resume():
    _enqueue_status(status_label_id, "Status: Resuming processes...")
    _enqueue_step("[RESUME] Resuming processes...")
    _enqueue_timer("")
    if not SUSPENDED:
        _enqueue_status(status_label_id, "Status: Nothing to resume.")
        _enqueue_step("[FAIL] No suspended processes")
        _enqueue_log("No suspended processes tracked.")
        return
    pid_list = set(SUSPENDED)
    _suspend_or_resume(pid_list, action="resume")
    resumed = sorted(pid_list)
    SUSPENDED.clear()
    _enqueue_status(status_label_id, f"Status: [OK] Resumed {len(resumed)} process(es).")
    _enqueue_step(f"[OK] Resumed {len(resumed)} process(es)")
    _enqueue_log(f"Resumed PIDs: {', '.join(map(str, resumed))}")


def pause_async():
    threading.Thread(target=_pause, daemon=True).start()


def resume_async():
    threading.Thread(target=_resume, daemon=True).start()


def _hss_switch_cycle():
    if not connect_location or not HSS_LOCATIONS:
        _enqueue_status(handler_label_id, "Handler: [FAIL] HSS handler unavailable.")
        _enqueue_step("[FAIL] HSS switcher not available")
        _enqueue_log("[hss] hss_switcher not available or no locations configured.")
        return

    cycle_count = 0
    while not handler_stop_event.is_set():
        try:
            cycle_count += 1
            _enqueue_status(handler_label_id, f"Handler: [RUNNING] HSS Cycle #{cycle_count}")
            _enqueue_log(f"[hss] ===== Starting Cycle #{cycle_count} =====")

            # Step 1: Find and pause processes
            _enqueue_step("Step 1/4: [SEARCH] Finding target processes...")
            _enqueue_timer("")
            pids = _collect_target_pids()
            if pids:
                _enqueue_step(f"Step 1/4: [PAUSE] Suspending {len(pids)} process(es)...")
                _suspend_or_resume(pids, action="suspend")
                _enqueue_log(f"[hss] Suspended: {', '.join(map(str, sorted(pids)))}")
            else:
                _enqueue_log("[hss] No target processes found.")

            # Step 2: Switch to random US location
            location = random.choice(HSS_LOCATIONS)
            _enqueue_step(f"Step 2/4: [SWITCH] Connecting to US server: {location}...")
            ok = connect_location(location)
            if ok:
                _enqueue_log(f"[hss] Connected to {location}")
            else:
                _enqueue_log(f"[hss] Failed to connect to {location}")

            # Step 3: Wait 10 seconds before resume
            _countdown_sleep(HSS_POST_DELAY_SEC, "Step 3/4: [WAIT] Waiting 10s before resume")

            # Step 4: Resume processes
            if pids:
                _enqueue_step(f"Step 4/4: [RESUME] Resuming {len(pids)} process(es)...")
                _suspend_or_resume(pids, action="resume")
                _enqueue_log(f"[hss] Resumed: {', '.join(map(str, sorted(pids)))}")

            # Wait 4 minutes until next cycle
            _enqueue_log(f"[hss] Cycle #{cycle_count} completed. Next cycle in 4 minutes...")
            _countdown_sleep(HSS_INTERVAL_SEC, "[IDLE] Next cycle in")
        except Exception as exc:  # noqa: BLE001
            _enqueue_status(handler_label_id, "Handler: [ERROR] Error occurred")
            _enqueue_step(f"[ERROR] {exc}")
            _enqueue_log(f"[hss] Error: {exc}")
            break

    _enqueue_status(handler_label_id, "Handler: [STOPPED]")
    _enqueue_step("[STOPPED] Handler stopped")
    _enqueue_timer("")
    _enqueue_log("[hss] Stopped HSS switch loop.")


def start_hss_handler():
    global handler_thread
    if handler_thread and handler_thread.is_alive():
        _enqueue_status(handler_label_id, "Handler: [WARN] Already running")
        _enqueue_step("[WARN] Handler already running")
        return
    if not connect_location:
        _enqueue_status(handler_label_id, "Handler: [FAIL] HSS handler unavailable")
        _enqueue_step("[FAIL] HSS switcher not available")
        _enqueue_log("[hss] Missing hss_switcher import.")
        return
    handler_stop_event.clear()
    handler_thread = threading.Thread(target=_hss_switch_cycle, daemon=True)
    handler_thread.start()
    _enqueue_status(handler_label_id, "Handler: [START] HSS handler running")
    _enqueue_step("[START] Starting HSS handler...")
    _enqueue_log("[hss] Started HSS switch loop.")


def stop_handler():
    if not handler_thread or not handler_thread.is_alive():
        _enqueue_status(handler_label_id, "Handler: [WARN] Not running")
        _enqueue_step("[WARN] Handler not running")
        return
    handler_stop_event.set()
    _enqueue_status(handler_label_id, "Handler: [STOP] Stopping...")
    _enqueue_step("[STOP] Stopping handler...")
    _enqueue_log("[handler] Stop requested.")


def build_ui():
    global status_label_id, handler_label_id, step_label_id, timer_label_id, log_widget_id

    with dpg.window(label="Process Control Panel", width=800, height=650) as main_win:
        dpg.add_text("=" * 90, color=(100, 100, 100))
        status_label_id = dpg.add_text("Status: Idle", color=(255, 255, 0))
        handler_label_id = dpg.add_text("Handler: Idle", color=(200, 200, 200))
        dpg.add_spacing(count=1)
        step_label_id = dpg.add_text("", color=(150, 200, 255))
        timer_label_id = dpg.add_text("", color=(255, 200, 100))
        dpg.add_text("=" * 90, color=(100, 100, 100))
        dpg.add_spacing(count=2)
        
        dpg.add_text("Controls:", color=(150, 255, 150))
        dpg.add_spacing(count=1)

        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Pause All", 
                width=240, 
                height=40,
                callback=lambda: pause_async()
            )
            dpg.add_button(
                label="Resume All", 
                width=240, 
                height=40,
                callback=lambda: resume_async()
            )
            dpg.add_button(
                label="Start HSS Switcher Handler", 
                width=280, 
                height=40,
                callback=lambda: start_hss_handler()
            )

        dpg.add_spacing(count=2)
        dpg.add_text("Log:", color=(200, 200, 200))
        log_widget_id = dpg.add_input_text(
            multiline=True,
            readonly=True,
            width=760,
            height=420,
            tab_input=False,
        )

    return main_win


def main():
    dpg.create_context()
    build_ui()
    dpg.create_viewport(title="Process Control Panel", width=820, height=710)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        _flush_ui()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()

