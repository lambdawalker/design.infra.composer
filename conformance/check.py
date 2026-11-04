"""Run an Infra Composer port's JSON test adapter against the reference vectors."""
import json
from pathlib import Path
import subprocess
import sys

def main(command):
    if not command:
        print("Usage: python3 conformance/check.py ADAPTER [ARG ...]", file=sys.stderr)
        return 2
    cases = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    failed = 0
    for case in cases:
        try:
            response = subprocess.run(command, input=json.dumps(case["input"]),
                                      capture_output=True, encoding="utf-8",
                                      timeout=30, check=True)
            actual = json.loads(response.stdout)
            # Canonical JSON also distinguishes true from 1.
            if json.dumps(actual, sort_keys=True) != json.dumps(case["expected"], sort_keys=True):
                raise ValueError("result differs from expected JSON")
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            failed += 1
            print(f"{case['id']}: {error}", file=sys.stderr)
    print(f"{len(cases) - failed}/{len(cases)} conformance cases passed")
    return int(bool(failed))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
