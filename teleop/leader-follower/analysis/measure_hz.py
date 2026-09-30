"""Measure the control-loop rate of the leader-follower teleop.

Runs the same loop as teleop.py, but wraps the three kinds of bus call
(leader read, follower read, follower write) with timers, so every cycle
records how many of each happened and how long each took. Prints stats at
the end and saves raw data. servo_control.py is not modified.

Usage (from teleop/leader-follower/analysis/):
    python measure_hz.py --label still --duration 30
    python measure_hz.py --label real --duration 30

Press SPACE (or wait for --duration, or Ctrl+C) to stop.
Results are saved to analysis/results/hz_<label>.npz and .png.
"""
import argparse
import os
import select
import sys
import termios
import time
import tty

import numpy as np

# servo_control.py lives one level up, in teleop/leader-follower/
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
RESULTS_DIR = os.path.join(HERE, "results")

import servo_control

BAUDRATE = 1000000
KINDS = ["leader_read", "follower_read", "follower_write"]


class CycleTally:
    """Accumulates bus-call counts and time for the current cycle."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = [0, 0, 0]
        self.time = [0.0, 0.0, 0.0]
        self.fails = 0

    def add(self, kind, dt, failed):
        self.count[kind] += 1
        self.time[kind] += dt
        self.fails += failed


def instrument(obj, method_name, kind, tally, comm_index):
    """Replace obj.method_name with a timed wrapper that reports to tally.

    comm_index is where comm_result sits in the method's return tuple
    (read2ByteTxRx -> (data, comm, err), WritePosEx -> (comm, err)).
    """
    original = getattr(obj, method_name)

    def timed(*args, **kwargs):
        t = time.perf_counter()
        result = original(*args, **kwargs)
        tally.add(kind, time.perf_counter() - t, result[comm_index] != 0)
        return result

    setattr(obj, method_name, timed)


def is_space_pressed():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1) == ' '
    return False


def summarize(name, dt):
    dt_ms = dt * 1e3
    return (f"{name:<14} n={len(dt):>6}  mean={1 / dt.mean():7.1f} Hz  "
            f"dt mean={dt_ms.mean():6.2f}  median={np.median(dt_ms):6.2f}  "
            f"p99={np.percentile(dt_ms, 99):6.2f}  max={dt_ms.max():7.2f} ms")


def report(t_start, counts, times, fails, warmup):
    dt = np.diff(t_start)[warmup:]         # cycle i duration = start[i+1] - start[i]
    c = counts[:-1][warmup:]               # (cycles, 3) bus calls per kind in cycle i
    tm = times[:-1][warmup:] * 1e3         # (cycles, 3) ms per kind in cycle i
    f = fails[:-1][warmup:]

    if len(dt) == 0:
        print("Not enough cycles recorded after warmup.")
        return

    print("\n=== Loop rate ===")
    print(summarize("all cycles", dt))

    writes = c[:, 2]
    print("\nBy follower writes per cycle (a joint skips its write when the goal is out of range):")
    for k in range(6, -1, -1):
        sel = writes == k
        if sel.sum() >= 10:
            print(summarize(f"{k} writes", dt[sel]))

    print("\n=== Bus calls (per call, ms) ===")
    for j, kind in enumerate(KINDS):
        n_calls = c[:, j].sum()
        if n_calls:
            per_call = tm[:, j].sum() / n_calls
            print(f"{kind:<15} calls/cycle={c[:, j].mean():5.2f}  mean={per_call:6.3f} ms")
    print(f"comm failures:  {int(f.sum())} over {len(dt)} cycles")

    print("\n=== Where the time goes (per cycle, ms) ===")
    for j, kind in enumerate(KINDS):
        print(f"{kind:<15} mean={tm[:, j].mean():6.3f}  ({100 * tm[:, j].mean() / (dt.mean() * 1e3):4.1f}%)")
    other = dt * 1e3 - tm.sum(axis=1)
    print(f"{'other':<15} mean={other.mean():6.3f}  ({100 * other.mean() / (dt.mean() * 1e3):4.1f}%)"
          "   <- Python, mapping math, prints")

    slow = dt > 3 * np.median(dt)
    print(f"\nSpikes (> 3x median dt): {slow.sum()} of {len(dt)} cycles")


def plot(path_png, t_start, counts, warmup, label):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipping plot (pip install matplotlib)")
        return
    dt = np.diff(t_start)[warmup:] * 1e3
    t = t_start[1:][warmup:] - t_start[0]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
    ax1.plot(t, 1e3 / dt, lw=0.6)
    ax1.set_xlabel("time (s)")
    ax1.set_ylabel("Hz")
    ax1b = ax1.twinx()
    ax1b.step(t, counts[:-1][warmup:, 2], color="tab:orange", lw=0.8)
    ax1b.set_ylabel("follower writes / cycle")
    ax1.set_title(f"Leader-follower teleop loop rate - {label}")
    ax2.hist(dt, bins=100)
    ax2.set_xlabel("cycle dt (ms)")
    ax2.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(path_png, dpi=120)
    print(f"Plot saved to {path_png}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run", help="still / real - used in output filenames")
    parser.add_argument("--duration", type=float, default=30.0, help="seconds to record")
    parser.add_argument("--warmup", type=int, default=20, help="cycles to drop from the start")
    parser.add_argument("--leader-port", default="/dev/ttyACM1")
    parser.add_argument("--follower-port", default="/dev/ttyACM0")
    args = parser.parse_args()

    print(f"Using leader port: {args.leader_port}")
    print(f"Using follower port: {args.follower_port}")

    servo = servo_control.Servo(args.leader_port, args.follower_port, BAUDRATE)
    if not servo.init_servos():
        return

    tally = CycleTally()
    instrument(servo.leader_servo, "read2ByteTxRx", 0, tally, comm_index=1)
    instrument(servo.follower_servo, "read2ByteTxRx", 1, tally, comm_index=1)
    instrument(servo.follower_servo, "WritePosEx", 2, tally, comm_index=0)

    # Pre-allocate generously so the loop never grows lists (keeps timing clean).
    max_cycles = int(args.duration * 1000) + 1
    t_start = np.zeros(max_cycles)
    counts = np.zeros((max_cycles, 3), dtype=np.int16)
    times = np.zeros((max_cycles, 3))
    fails = np.zeros(max_cycles, dtype=np.int16)
    n = 0

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    print(f"Recording '{args.label}' for {args.duration:.0f} s - press SPACE to stop early.")
    try:
        tty.setcbreak(fd)
        t0 = time.perf_counter()
        while n < max_cycles:
            ts = time.perf_counter()
            if ts - t0 > args.duration or is_space_pressed():
                break
            tally.reset()

            for i in servo_control.leader_limits.keys():
                result, pos = servo.read(i)
                if result:
                    servo.move(i, pos)

            t_start[n] = ts
            counts[n] = tally.count
            times[n] = tally.time
            fails[n] = tally.fails
            n += 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        servo.shutdown()

    t_start, counts, times, fails = t_start[:n], counts[:n], times[:n], fails[:n]
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, f"hz_{args.label}")
    np.savez(f"{out}.npz", t_start=t_start, counts=counts, times=times, fails=fails,
             kinds=np.array(KINDS))
    if n > 1:
        print(f"\nRecorded {n} cycles in {t_start[-1] - t_start[0]:.1f} s -> {out}.npz")

    if n > args.warmup + 2:
        report(t_start, counts, times, fails, args.warmup)
        plot(f"{out}.png", t_start, counts, args.warmup, args.label)


if __name__ == "__main__":
    main()
