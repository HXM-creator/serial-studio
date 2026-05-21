#!/usr/bin/env python3
"""Send test sine-wave data over serial — for testing Serial Studio.

Usage:
  python tools/test_sender.py COM3        # real port
  python tools/test_sender.py              # print to console (pipe to virtual port)
"""

import argparse
import math
import sys
import time

try:
    import serial
except ImportError:
    serial = None


def generate_line(t: float) -> str:
    ch1 = 50 + 40 * math.sin(t * 0.5)
    ch2 = 30 + 25 * math.cos(t * 0.7 + 1.2)
    ch3 = 20 * math.sin(t * 1.3) * math.cos(t * 0.3)
    return f"{ch1:.1f}, {ch2:.1f}, {ch3:.2f}"


def main():
    parser = argparse.ArgumentParser(description="Serial Studio test data sender")
    parser.add_argument("port", nargs="?", help="Serial port (omit for console output)")
    parser.add_argument("-b", "--baud", type=int, default=115200)
    parser.add_argument("-r", "--rate", type=float, default=20, help="Messages per second")
    args = parser.parse_args()

    t = 0.0
    dt = 1.0 / args.rate

    ser = None
    if args.port and serial:
        ser = serial.Serial(args.port, args.baud)

    try:
        while True:
            line = generate_line(t)
            if ser:
                ser.write((line + "\n").encode())
            else:
                print(line, flush=True)
            t += dt
            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        if ser:
            ser.close()


if __name__ == "__main__":
    main()
