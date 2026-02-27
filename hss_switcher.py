import time
import itertools
import pyautogui as pag
import pygetwindow as gw

# List of locations to cycle through. Edit as needed.
LOCATIONS = [
    "United States",
    "Atlanta",
    "Boston",
    "Charlotte",
    "Chicago",
    "Columbus",
    "Dallas",
    "Denver",
    "Houston",
    "Indianapolis",
    "Kansas City",
    "Las Vegas",
    "Los Angeles",
    "Miami",
    "Minneapolis",
    "New York",
    "Orlando",
    "Philadelphia",
    "Phoenix",
    "Portland",
    "San Francisco",
    "San Jose",
    "St. Louis",
    "San Francisco",
    "Seattle",
    "Washington DC",
]

INTERVAL_SEC = 120         # Every 2 minutes
POST_CONNECT_DELAY = 15    # Wait 15 seconds after switching


def focus_hss() -> bool:
    """Activate a Hotspot Shield window if present."""
    titles = [t for t in gw.getAllTitles() if t and "hotspot" in t.lower()]
    if not titles:
        return False
    try:
        win = gw.getWindowsWithTitle(titles[0])[0]
        win.activate()
        time.sleep(0.5)
        return True
    except Exception:
        return False


def connect_location(location: str) -> bool:
    """Open search via Ctrl+Shift+V, type location, press Enter to connect."""
    if not focus_hss():
        print("Could not find/activate Hotspot Shield window.")
        return False

    pag.hotkey("ctrl", "shift", "v")
    time.sleep(0.5)

    pag.typewrite(location, interval=0.03)
    time.sleep(0.3)

    # Move focus to the first result, then activate Connect.
    pag.press("tab")   # focus into results list
    pag.press("down")  # select the first result
    time.sleep(0.1)
    pag.press("enter") # trigger Connect

    print(f"Requested connect to: {location}")
    return True


def main():
    for loc in itertools.cycle(LOCATIONS):
        connect_location(loc)
        time.sleep(POST_CONNECT_DELAY)

        slept = 0
        while slept < INTERVAL_SEC:
            time.sleep(1)
            slept += 1


if __name__ == "__main__":
    main()

