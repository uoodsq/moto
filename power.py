#!/usr/bin/env python
from collections import namedtuple
import json
import sys


DownstreamChannel = namedtuple(
    "DownstreamChannel",
    [
        "channel",
        "lock_status",
        "modulation",
        "channel_id",
        "frequency",
        "power",
        "snr",
        "corrected",
        "uncorrected",
    ],
)
UpstreamChannel = namedtuple(
    "UpstreamChannel",
    [
        "channel",
        "lock_status",
        "channel_type",
        "channel_id",
        "symbol_rate",
        "frequency",
        "power",
    ],
)


for line in sys.stdin.readlines():
    try:
        line = json.loads(line)
    except json.JSONDecodeError:
        print(line)
        raise

    print(line["ts"])
    print("downstream:")
    for channel in line["downstream"].split("|+|"):
        channel = DownstreamChannel(*channel.strip("^").split("^"))
        print(channel)
    print("upstream:")
    for channel in line["upstream"].split("|+|"):
        channel = UpstreamChannel(*channel.strip("^").split("^"))
        print(channel)
    print("\n")

