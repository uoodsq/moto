#!/usr/bin/env python
from argparse import ArgumentParser
from datetime import datetime
import json
import sys


parser = ArgumentParser()
parser.add_argument("--grep", "-g")

args = parser.parse_args()


timestamps = set()
logs = []


for line in sys.stdin.readlines():
    line = line.strip('" ')

    for log in line.split("}-{"):
        if "Time Not Established" in log:
            ts = None
            log = log[len("Time Not Established^") :]
        else:
            try:
                ts_str, log = log.split("\\n", maxsplit=1)
            except ValueError:
                print(log)
                sys.exit(1)
            ts = datetime.strptime(ts_str, "%H:%M:%S^%a %b %d %Y")

        if ts and ts in timestamps:
            continue

        timestamps.add(ts)

        log = log.strip("^ ")
        priority, log = log.split("^", maxsplit=1)

        if log.endswith('"\n'):
            log = log[:-2]

        if not args.grep or (args.grep in priority or args.grep in log):
            logs.append({"ts": ts and ts.isoformat(), "priority": priority, "msg": log})


for log in logs:
    print(json.dumps(log))
