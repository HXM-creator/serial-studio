#!/usr/bin/env python3
"""Test sender that outputs microlog-style formatted data.

Simulates what an STM32/ESP32 would send when using microlog.
Useful for testing Serial Studio with realistic-looking data.
"""

import argparse
import math
import random
import time

try:
    import serial
except ImportError:
    serial = None

LEVELS = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR"]
COLOURS = {
    "TRACE": "\033[90m", "DEBUG": "\033[36m", "INFO": "\033[32m",
    "WARN": "\033[33m", "ERROR": "\033[31m",
}
RESET = "\033[0m"


def generate(t: float):
    sensor1 = 50 + 40 * math.sin(t * 0.3)
    sensor2 = 30 + 25 * math.cos(t * 0.5 + 0.8)
    sensor3 = random.uniform(0, 100)

    yield "INFO", f"System running | sensor1={sensor1:.1f} sensor2={sensor2:.1f}"

    if sensor3 > 80:
        yield "WARN", f"Sensor 3 high: {sensor3:.1f} (threshold 80)"

    if int(t) % 10 == 0 and t - int(t) < 0.05:
        yield "INFO", f"Stats: ch1={sensor1:.2f} ch2={sensor2:.2f} ch3={sensor3:.2f}"

    if random.random() < 0.02:
        yield "ERROR", "I2C timeout on bus 1, retrying..."

    # Pure numeric line for plotting
    yield "DATA", f"{sensor1:.1f}, {sensor2:.1f}, {sensor3:.1f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", help="Serial port")
    parser.add_argument("-b", "--baud", type=int, default=115200)
    parser.add_argument("-r", "--rate", type=float, default=10)
    parser.add_argument("--colour", action="store_true", help="ANSI colour output")
    args = parser.parse_args()

    t = 0.0
    dt = 1.0 / args.rate

    ser = None
    if args.port and serial:
        ser = serial.Serial(args.port, args.baud)

    try:
        while True:
            for level, msg in generate(t):
                if level == "DATA":
                    line = msg
                elif args.colour:
                    line = f"{COLOURS[level]}[{level}]{RESET} {msg}"
                else:
                    line = f"[{level}] {msg}"

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
