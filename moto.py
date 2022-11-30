#!/usr/bin/env python
"""
Used to manage and pull stats from a Motorola MB8600 modem (and possibly others).
"""
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Generator

import requests
from dateutil.parser import parse as parse_datetime


@dataclass
class Log:
    """
    A parsed log entry from the modem.
    """

    timestamp: datetime
    level: str
    message: str


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


def main():
    """
    Log in to the modem and pull all the known statistics.
    """
    login(MODEM_USERNAME, MODEM_PASSWORD)

    results = do_actions(*KNOWN_ACTIONS)

    print(json.dumps({"ts": datetime.now().isoformat(), "data": results}))


if __name__ == "__main__":
    main()
