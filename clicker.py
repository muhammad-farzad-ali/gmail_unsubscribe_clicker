import csv
import os
import sys
import time
import signal

import pyautogui
from pynput import mouse, keyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

CLICKS_CSV = "clicks.csv"
RECORDING_MODE = "record"
WAITING_FOR_DELAY = "waiting_delay"
WAITING_FOR_COUNT = "waiting_count"
RUNNING = "running"

state = {
    "mode": RECORDING_MODE,
    "clicks": [],
    "temp_clicks": [],
    "loop_delay": 2.0,
    "loop_count": None,
    "current_index": 0,
    "loop_iteration": 0,
    "running": False,
}


def signal_handler(sig, frame):
    print("\nStopped.")
    state["running"] = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def save_clicks(clicks, filepath=CLICKS_CSV):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y"])
        for x, y in clicks:
            writer.writerow([x, y])
    print(f"Saved {len(clicks)} clicks to {filepath}")


def load_clicks(filepath=CLICKS_CSV):
    if not os.path.exists(filepath):
        return []
    clicks = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clicks.append((int(row["x"]), int(row["y"])))
    return clicks


def do_click(x, y):
    pyautogui.click(x, y)


def run_loop():
    clicks = state["clicks"]
    delay = state["loop_delay"]
    count = state["loop_count"]
    i = 0
    state["running"] = True

    print(
        f"\nStarting loop: {'infinite' if count is None else count} iterations, {delay}s delay"
    )
    print("Press Ctrl+C to stop.\n")

    try:
        while state["running"] and (count is None or i < count):
            i += 1
            label = f"Loop {i}" if count else f"Iteration {i}"
            print(f"{label}: clicking {len(clicks)} positions...")

            for idx, (x, y) in enumerate(clicks):
                if not state["running"]:
                    break
                print(f"  Click {idx + 1}/{len(clicks)} at ({x}, {y})")
                do_click(x, y)
                time.sleep(0.1)

            if state["running"]:
                print(f"  Waiting {delay}s before next loop...\n")
                time.sleep(delay)

        print(f"Done. Completed {i} iteration(s).")
    except KeyboardInterrupt:
        print(f"\nInterrupted after {i} iteration(s).")


def on_click(x, y, button, pressed):
    if not pressed:
        return True
    if state["mode"] != RECORDING_MODE:
        return True
    state["temp_clicks"].append((x, y))
    print(f"Recorded click #{len(state['temp_clicks'])}: ({x}, {y})")
    return True


def setup():
    print("=== Screen Auto Clicker ===\n")
    print("RECORDING MODE")
    print("  - Click on the screen to record positions.")
    print("  - Press F2 when done recording.")
    print()


def record_clicks():
    state["mode"] = RECORDING_MODE
    state["temp_clicks"] = []
    print("Recording clicks now. Press F2 to finish recording.\n")

    mouse_listener = mouse.Listener(on_click=on_click)

    done = keyboard.Listener(
        on_press=lambda key: state.__setitem__("record_done", True)
        if key == keyboard.Key.f2
        else None
    )

    state["record_done"] = False
    mouse_listener.start()
    done.start()

    try:
        while not state["record_done"]:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        mouse_listener.stop()
        done.stop()
        mouse_listener.join()
        done.join()

    print(f"\nRecorded {len(state['temp_clicks'])} clicks.")
    return state["temp_clicks"]


def ask_loop():
    while True:
        answer = (
            input("Loop over these clicks with a 2s delay? (y/n): ").strip().lower()
        )
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def ask_loop_count():
    while True:
        answer = (
            input("How many times to loop? (Enter 0 or 'inf' for unlimited): ")
            .strip()
            .lower()
        )
        if answer in ("0", "inf", "infinite", ""):
            return None
        try:
            n = int(answer)
            if n > 0:
                return n
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Enter a number or 0 for unlimited.")


def main():
    setup()

    existing = load_clicks()
    if existing:
        print(f"Found existing clicks.csv with {len(existing)} clicks.")
        use_existing = input("Use existing recorded clicks? (y/n): ").strip().lower()
        if use_existing in ("y", "yes"):
            state["clicks"] = existing
            print("Loaded existing clicks:")
            for i, (x, y) in enumerate(state["clicks"], 1):
                print(f"  {i}. ({x}, {y})")
        else:
            clicks = record_clicks()
            if not clicks:
                print("No clicks recorded. Exiting.")
                return
            state["clicks"] = clicks
            save_clicks(clicks)
    else:
        clicks = record_clicks()
        if not clicks:
            print("No clicks recorded. Exiting.")
            return
        state["clicks"] = clicks
        save_clicks(clicks)

    if not ask_loop():
        print("Exiting.")
        return

    state["loop_count"] = ask_loop_count()
    run_loop()


if __name__ == "__main__":
    main()
