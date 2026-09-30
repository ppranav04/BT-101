"""Measure the control-loop rate of the joystick teleop.

Runs the same loop as controller.py, but records a timestamp every cycle,
how many joints were being driven (vs. held), and how long the input read
and the servo bus calls took. Prints stats at the end and saves raw data.

Usage (from teleop/joystick/analysis/):
    python measure_hz.py --label idle --duration 30
    python measure_hz.py --label moving --duration 30
    python measure_hz.py --label real --duration 60

Press START (or wait for --duration, or Ctrl+C) to stop.
Results are saved to analysis/results/hz_<label>.npz and .png.
"""
import argparse
import os
import sys
import time

import numpy as np
import pygame as pg

# controller.py and servo_control.py live one level up, in teleop/joystick/
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
RESULTS_DIR = os.path.join(HERE, "results")

import servo_control
from controller import SERIAL_PORT, BAUDRATE, mapping, init_controllers, XboxCtrl

DEADZONE = 1638  # must match the axis deadzone in controller.py / servo_control.move()


def read_dirs(xbox):
    """Same input translation as controller.py's loop, for all 6 joints."""
    dirs = {}
    for i in mapping.keys():
        if 1 <= i <= 4:
            dirs[i] = xbox.get_axis(mapping[i])
        elif i == 5:
            left, right = mapping[i]
            if xbox.get_button(left):
                dirs[i] = -1
            elif xbox.get_button(right):
                dirs[i] = 1
            else:
                dirs[i] = 0
        else:
            left, right = mapping[i]
            if xbox.get_axis(left) > DEADZONE:
                dirs[i] = -1
            elif xbox.get_axis(right) > DEADZONE:
                dirs[i] = 1
            else:
                dirs[i] = 0
    return dirs


def is_moving(servo_id, d):
    """True if move() will only write (1 round trip); False if it reads + writes (2)."""
    if 1 <= servo_id <= 4:
        return not (-DEADZONE <= d <= DEADZONE)
    return d != 0


def summarize(name, dt):
    dt_ms = dt * 1e3
    return (f"{name:<14} n={len(dt):>6}  mean={1 / dt.mean():7.1f} Hz  "
            f"dt mean={dt_ms.mean():6.2f}  median={np.median(dt_ms):6.2f}  "
            f"p99={np.percentile(dt_ms, 99):6.2f}  max={dt_ms.max():7.2f} ms")


def report(t_start, n_moving, t_input, t_bus, warmup):
    dt = np.diff(t_start)[warmup:]            # cycle i duration = start[i+1] - start[i]
    moving = n_moving[:-1][warmup:]           # state during cycle i
    t_in = t_input[:-1][warmup:] * 1e3
    t_b = t_bus[:-1][warmup:] * 1e3

    if len(dt) == 0:
        print("Not enough cycles recorded after warmup.")
        return

    print("\n=== Loop rate ===")
    print(summarize("all cycles", dt))
    print("\nBy number of joints moving (0 = all held = 12 round trips, 6 = 6 round trips):")
    for k in range(7):
        sel = moving == k
        if sel.sum() >= 10:
            print(summarize(f"{k} moving", dt[sel]) + f"   bus/trip={t_b[sel].mean() / (12 - k):5.2f} ms")

    print("\n=== Where the time goes (per cycle, ms) ===")
    print(f"input (pump + reads): mean={t_in.mean():6.3f}  p99={np.percentile(t_in, 99):6.3f}")
    print(f"servo bus (6x move):  mean={t_b.mean():6.3f}  p99={np.percentile(t_b, 99):6.3f}")
    other = dt * 1e3 - t_in - t_b
    print(f"other/overhead:       mean={other.mean():6.3f}")

    slow = dt * 1e3 > 3 * np.median(dt * 1e3)
    print(f"\nSpikes (> 3x median dt): {slow.sum()} of {len(dt)} cycles")


def plot(path_png, t_start, n_moving, warmup, label):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipping plot (pip install matplotlib)")
        return
    dt = np.diff(t_start)[warmup:] * 1e3
    t = (t_start[1:][warmup:] - t_start[0])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
    ax1.plot(t, 1e3 / dt, lw=0.6, label="loop Hz")
    ax1.set_xlabel("time (s)")
    ax1.set_ylabel("Hz")
    ax1b = ax1.twinx()
    ax1b.step(t, n_moving[:-1][warmup:], color="tab:orange", lw=0.8, label="joints moving")
    ax1b.set_ylabel("joints moving")
    ax1.set_title(f"Joystick teleop loop rate - {label}")
    ax2.hist(dt, bins=100)
    ax2.set_xlabel("cycle dt (ms)")
    ax2.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(path_png, dpi=120)
    print(f"Plot saved to {path_png}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run", help="idle / moving / real - used in output filenames")
    parser.add_argument("--duration", type=float, default=30.0, help="seconds to record")
    parser.add_argument("--warmup", type=int, default=20, help="cycles to drop from the start")
    args = parser.parse_args()

    if init_controllers() == 0:
        print("No controller found.")
        return
    xbox = XboxCtrl()
    servo = servo_control.Servo(SERIAL_PORT, BAUDRATE)
    if not servo.init_servo():
        print("Servo initialisation failed")
        return

    # Pre-allocate generously so the loop never grows lists (keeps timing clean).
    max_cycles = int(args.duration * 2000) + 1
    t_start = np.zeros(max_cycles)
    t_input = np.zeros(max_cycles)
    t_bus = np.zeros(max_cycles)
    n_moving = np.zeros(max_cycles, dtype=np.int8)
    n = 0

    print(f"Recording '{args.label}' for {args.duration:.0f} s - press START to stop early.")
    try:
        t0 = time.perf_counter()
        while n < max_cycles:
            ts = time.perf_counter()
            if ts - t0 > args.duration:
                break
            pg.event.pump()
            if xbox.get_button(pg.CONTROLLER_BUTTON_START):
                break
            dirs = read_dirs(xbox)
            t_in_end = time.perf_counter()

            for i, d in dirs.items():
                servo.move(i, d)
            t_bus_end = time.perf_counter()

            t_start[n] = ts
            t_input[n] = t_in_end - ts
            t_bus[n] = t_bus_end - t_in_end
            n_moving[n] = sum(is_moving(i, d) for i, d in dirs.items())
            n += 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        servo.shutdown()

    t_start, t_input, t_bus, n_moving = t_start[:n], t_input[:n], t_bus[:n], n_moving[:n]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, f"hz_{args.label}")
    np.savez(f"{out}.npz", t_start=t_start, t_input=t_input, t_bus=t_bus, n_moving=n_moving)
    print(f"\nRecorded {n} cycles in {t_start[-1] - t_start[0]:.1f} s -> {out}.npz" if n > 1 else "No data.")

    if n > args.warmup + 2:
        report(t_start, n_moving, t_input, t_bus, args.warmup)
        plot(f"{out}.png", t_start, n_moving, args.warmup, args.label)


if __name__ == "__main__":
    main()
