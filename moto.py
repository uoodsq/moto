#!/usr/bin/env python
"""
Used to manage and pull stats from a Motorola MB8600 modem (and possibly others).
"""
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Generator

import requests
import urllib3
from dateutil.parser import parse as parse_datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger("rich")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MODEM_HOSTNAME = "192.168.100.1"
MODEM_USERNAME = os.getenv("MODEM_USERNAME", "admin")
MODEM_PASSWORD = os.getenv("MODEM_PASSWORD", "motorola")

HNAP_URI = f"https://{MODEM_HOSTNAME}/HNAP1/"
SOAP_NAMESPACE = "http://purenetworks.com/HNAP1/"

KNOWN_ACTIONS = [
    "GetHomeConnection",
    "GetHomeAddress",
    "GetMotoStatusSoftware",
    "GetMotoStatusLog",
    "GetMotoLagStatus",
    "GetMotoStatusConnectionInfo",
    "GetMotoStatusDownstreamChannelInfo",
    "GetMotoStatusStartupSequence",
    "GetMotoStatusUpstreamChannelInfo",
]


@dataclass
class Log:
    """
    A parsed log entry from the modem.
    """

    timestamp: datetime
    level: str
    message: str

    def __lt__(self, other):
        return self.timestamp < other.timestamp


@dataclass
class DownstreamChannel:
    """
    A parsed downstream channel from the modem.
    """

    channel: int
    lock_status: str
    modulation: str
    channel_id: int
    frequency: Decimal
    power: Decimal
    snr: Decimal
    corrected: int
    uncorrected: int

    def __lt__(self, other):
        return self.channel < other.channel


@dataclass
class UpstreamChannel:
    """
    A parsed upstream channel from the modem.
    """

    channel: int
    lock_status: str
    channel_type: str
    channel_id: int
    symbol_rate: Decimal
    frequency: Decimal
    power: Decimal

    def __lt__(self, other):
        return self.channel < other.channel


session = requests.Session()
session.verify = False


def millis():
    """
    Return the current time in milliseconds.
    """
    return int(round(time.time() * 1000)) % 2000000000000


def md5sum(key, data):
    """
    Return the MD5 hash of the given data, using the given key.
    """
    md5 = hmac.new(key.encode("utf-8"), digestmod=hashlib.md5)
    md5.update(data.encode("utf-8"))
    return md5.hexdigest()


def hnap_auth(key, data):
    """
    Return the HNAP_AUTH header value for the given data, using the given key.
    """
    return md5sum(key, data).upper() + " " + str(millis())


def do_action(action, params):
    """
    Perform an HNAP action with the given parameters.
    """
    action_uri = f'"{SOAP_NAMESPACE}{action}"'
    private_key = session.cookies.get("PrivateKey", path="/", default="withoutloginkey")

    response = session.post(
        HNAP_URI,
        data=json.dumps({action: params}),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "SOAPAction": action_uri,
            "HNAP_AUTH": hnap_auth(private_key, str(millis()) + action_uri),
        },
    )

    try:
        response = json.loads(response.content.strip())
    except json.JSONDecodeError:
        print(response.content)
        raise

    return response[action + "Response"]


def do_actions(*actions):
    """
    Perform multiple HNAP actions at once.
    """
    return do_action("GetMultipleHNAPs", {action: "" for action in actions})


def get_logs() -> Generator[Log, None, None]:
    """
    Fetch logs from the modem and return an iterator of log objects.
    """
    response = do_action("GetMotoStatusLog", {})

    return parse_logs(response["MotoStatusLogList"])


def parse_logs(logs) -> Generator[Log, None, None]:
    """
    Parse a raw log string into a generator of Log objects.
    """
    for line in logs.split("}-{"):
        yield parse_log(line)


def parse_log(line) -> Log:
    """
    Parse an individual log line into a Log object.
    """
    timestamp_str, line = line.split("\n", 1)
    timestamp = parse_datetime(timestamp_str.replace("^", " "))
    level, line = line.lstrip("^").split("^", 1)

    return Log(timestamp, level, line)


def login(username, password):
    """
    Login to the modem.
    """
    response = do_action(
        "Login",
        {
            "Action": "request",
            "Captcha": "",
            "LoginPassword": "",
            "PrivateLogin": "LoginPassword",
            "Username": username,
        },
    )

    private_key = md5sum(
        response["PublicKey"] + password, response["Challenge"]
    ).upper()

    session.cookies.set("uid", response["Cookie"], path="/")
    session.cookies.set("PrivateKey", private_key, path="/")

    response = do_action(
        "Login",
        {
            "Action": "login",
            "Captcha": "",
            "LoginPassword": md5sum(private_key, response["Challenge"]).upper(),
            "PrivateLogin": "LoginPassword",
            "Username": username,
        },
    )

    return response


def get_downstream_channels() -> Generator[DownstreamChannel, None, None]:
    """
    Get the downstream levels from the modem.
    """
    results = do_action("GetMotoStatusDownstreamChannelInfo", {})

    return parse_downstream_channels(results["MotoConnDownstreamChannel"])


def parse_downstream_channels(channels_str) -> Generator[DownstreamChannel, None, None]:
    """
    Parse the downstream channels string into a generator of downstream channel objects.
    """
    for line in channels_str.split("|+|"):
        yield parse_downstream_channel(line)


def parse_downstream_channel(channel_str) -> DownstreamChannel:
    """
    Parse an individual downstream channel string into a downstream channel object.
    """
    channel, channel_str = channel_str.split("^", 1)
    channel = int(channel)
    lock_status, channel_str = channel_str.split("^", 1)
    modulation, channel_str = channel_str.split("^", 1)
    channel_id, channel_str = channel_str.split("^", 1)
    channel_id = int(channel_id)
    frequency, channel_str = channel_str.split("^", 1)
    frequency = Decimal(frequency)
    power, channel_str = channel_str.split("^", 1)
    power = Decimal(power)
    snr, channel_str = channel_str.split("^", 1)
    snr = Decimal(snr)
    corrected, channel_str = channel_str.split("^", 1)
    corrected = int(corrected)
    uncorrected, channel_str = channel_str.split("^", 1)
    uncorrected = int(uncorrected.rstrip("^"))

    return DownstreamChannel(
        channel,
        lock_status,
        modulation,
        channel_id,
        frequency,
        power,
        snr,
        corrected,
        uncorrected,
    )


def get_upstream_channels():
    """
    Get the upstream levels from the modem.
    """
    results = do_action("GetMotoStatusUpstreamChannelInfo", {})

    return parse_upstream_channels(results["MotoConnUpstreamChannel"])


def parse_upstream_channels(channels_str) -> Generator[UpstreamChannel, None, None]:
    """
    Parse the upstream channels string into a generator of upstream channel objects.
    """
    for line in channels_str.split("|+|"):
        yield parse_upstream_channel(line)


def parse_upstream_channel(channel_str) -> UpstreamChannel:
    """
    Parse an individual upstream channel string into a upstream channel object.
    """
    channel, channel_str = channel_str.split("^", 1)
    channel = int(channel)
    lock_status, channel_str = channel_str.split("^", 1)
    channel_type, channel_str = channel_str.split("^", 1)
    channel_id, channel_str = channel_str.split("^", 1)
    channel_id = int(channel_id)
    symbol_rate, channel_str = channel_str.split("^", 1)
    symbol_rate = Decimal(symbol_rate)
    frequency, channel_str = channel_str.split("^", 1)
    frequency = Decimal(frequency)
    power, channel_str = channel_str.split("^", 1)
    power = Decimal(power.rstrip("^"))

    return UpstreamChannel(
        channel,
        lock_status,
        channel_type,
        channel_id,
        symbol_rate,
        frequency,
        power,
    )


def logs_command():
    """
    Log in to the modem and pull all the known statistics.
    """
    console = Console()
    table = Table("Timestamp", "Level", "Message")
    login(MODEM_USERNAME, MODEM_PASSWORD)

    for log in sorted(get_logs()):
        table.add_row(log.timestamp.isoformat(), log.level, log.message)

    console.print(table)


def levels_command():
    """
    Log into the modem and pull current downstream and upstream power levels.
    """
    console = Console()
    login(MODEM_USERNAME, MODEM_PASSWORD)

    table = Table(
        "Channel",
        "Lock Status",
        "Modulation",
        "Channel ID",
        "Frequency",
        "Power",
        "SNR",
        "Corrected",
        "Uncorrected",
    )

    for channel in sorted(get_downstream_channels()):
        table.add_row(
            str(channel.channel),
            channel.lock_status,
            channel.modulation,
            str(channel.channel_id),
            str(channel.frequency),
            str(channel.power),
            str(channel.snr),
            str(channel.corrected),
            str(channel.uncorrected),
        )

    console.print(table)

    table = Table(
        "Channel",
        "Lock Status",
        "Channel Type",
        "Channel ID",
        "Symbol Rate",
        "Frequency",
        "Power",
    )

    for level in sorted(get_upstream_channels()):
        table.add_row(
            str(level.channel),
            level.lock_status,
            level.channel_type,
            str(level.channel_id),
            str(level.symbol_rate),
            str(level.frequency),
            str(level.power),
        )

    console.print(table)


def dump_command():
    """
    Log in to the modem and pull all the known statistics.
    """
    login(MODEM_USERNAME, MODEM_PASSWORD)

    results = do_actions(*KNOWN_ACTIONS)

    print(json.dumps({"ts": datetime.now().isoformat(), "data": results}))


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()

    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser("dump")
    subparser.set_defaults(fn=dump_command)

    subparser = subparsers.add_parser("logs")
    subparser.set_defaults(fn=logs_command)

    subparser = subparsers.add_parser("levels")
    subparser.set_defaults(fn=levels_command)

    args = parser.parse_args()

    args.fn()
