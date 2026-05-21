"""Data parser: converts serial lines into float arrays."""

import re
from typing import Optional


def parse_line(line: str) -> Optional[list[float]]:
    """Try to parse a line of serial data into a list of floats.

    Supported formats (auto-detected):
      "12.3, 45.6, 78.9"    — comma separated
      "12.3 45.6 78.9"      — space  separated
      "ch1=12.3 ch2=45.6"   — labelled (keys are stripped)
      "12.3\t45.6"           — tab    separated
    """
    line = line.strip()
    if not line:
        return None

    # Try comma first
    if ',' in line:
        parts = [p.strip() for p in line.split(',')]
    else:
        # Split on whitespace (space or tab)
        parts = line.split()

    values = []
    for p in parts:
        # Strip optional label: "ch1=12.3" -> "12.3"
        if '=' in p:
            p = p.split('=')[1]
        try:
            values.append(float(p))
        except ValueError:
            # Skip non-numeric tokens — lets us ignore log text
            continue

    return values if values else None
