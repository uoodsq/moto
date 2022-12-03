"""
Contains classes used to communicate with an MB8600 modem (and possibly others that use the
same HNAP API).
"""
import hashlib
import hmac
import json
import os
from time import time
from typing import Generator

import urllib3
from requests import Session

from .downstream_channel import DownstreamChannel
from .modem_log import ModemLog
from .upstream_channel import UpstreamChannel

_KNOWN_ACTIONS = {
    "Login",
    "GetHomeConnection",
    "GetHomeAddress",
    "GetMotoStatusSoftware",
    "GetMotoStatusLog",
    "GetMotoLagStatus",
    "GetMotoStatusConnectionInfo",
    "GetMotoStatusDownstreamChannelInfo",
    "GetMotoStatusStartupSequence",
    "GetMotoStatusUpstreamChannelInfo",
}

_SOAP_NAMESPACE = "http://purenetworks.com/HNAP1/"

# NOTE: Bad security practice, but the modem uses a self-signed certificate.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MotoError(Exception):
    """
    Raised when an error occurs while communicating with the modem.
    """


class MotoClient:
    """
    A client for communicating with a Motorola modem.
    """

    _hostname: str
    _username: str
    _password: str

    def __init__(
        self,
        hostname: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self._hostname = hostname or os.environ.get("MOTO_HOSTNAME", "192.168.100.1")
        self._username = username or os.environ.get("MOTO_USERNAME", "admin")
        self._password = password or os.environ.get("MOTO_PASSWORD", "motorola")

        self._session = Session()

        # NOTE: Bad security practice, but the modem uses a self-signed certificate.
        self._session.verify = False

    def login(self):
        """
        Login to the modem.
        """
        response = self._do_action(
            "Login",
            {
                "Action": "request",
                "Captcha": "",
                "PrivateLogin": "LoginPassword",
                "Username": self._username,
                "LoginPassword": "",
            },
        )

        public_key = response["PublicKey"]
        challenge = response["Challenge"]

        self._private_key = self._md5sum(public_key + self._password, challenge)
        self._uid = response["Cookie"]

        login_password = self._md5sum(self._private_key, challenge)

        return self._do_action(
            "Login",
            {
                "Action": "login",
                "Captcha": "",
                "PrivateLogin": "LoginPassword",
                "Username": self._username,
                "LoginPassword": login_password,
            },
        )

    def get_logs(self) -> Generator[ModemLog, None, None]:
        """
        Get logs from the modem.
        """
        response = self._do_action("GetMotoStatusLog", {})

        return ModemLog.from_response(response["MotoStatusLogList"])

    def get_downstream_channels(self) -> Generator[DownstreamChannel, None, None]:
        """
        Get downstream channels from the modem.
        """
        response = self._do_action("GetMotoStatusDownstreamChannelInfo", {})

        return DownstreamChannel.from_response(response["MotoConnDownstreamChannel"])

    def get_upstream_channels(self) -> Generator[UpstreamChannel, None, None]:
        """
        Get upstream channels from the modem.
        """
        response = self._do_action("GetMotoStatusUpstreamChannelInfo", {})

        return UpstreamChannel.from_response(response["MotoConnUpstreamChannel"])

    @property
    def _cookies(self):
        return self._session.cookies

    @property
    def _hnap_uri(self) -> str:
        return f"https://{self._hostname}/HNAP1/"

    @property
    def _private_key(self) -> str:
        return self._cookies.get("PrivateKey", path="/", default="withoutloginkey")

    @_private_key.setter
    def _private_key(self, value):
        self._cookies.set("PrivateKey", value, path="/")

    @property
    def _uid(self) -> str:
        return self._cookies.get("uid", path="/")

    @_uid.setter
    def _uid(self, value):
        self._cookies.set("uid", value, path="/")

    @staticmethod
    def _timestamp() -> str:
        """
        Return the current timestamp in milliseconds.
        """
        return str(int(round(time() * 1000)) % 2000000000000)

    @staticmethod
    def _md5sum(key, data) -> str:
        """
        Return the MD5 hash of the given data, using the given key.
        """
        md5 = hmac.new(key.encode("utf-8"), digestmod=hashlib.md5)
        md5.update(data.encode("utf-8"))

        return md5.hexdigest().upper()

    def _hnap_auth(self, action: str) -> str:
        timestamp = self._timestamp()

        data = timestamp + _SOAP_NAMESPACE + action

        md5sum = self._md5sum(self._private_key, data)

        return f"{md5sum} {timestamp}"

    def _do_action(self, action, params):
        if action not in _KNOWN_ACTIONS:
            raise ValueError(f"Unknown action: {action}")

        action_uri = _SOAP_NAMESPACE + action

        response = self._session.post(
            self._hnap_uri,
            data=json.dumps({action: params}),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "SOAPAction": action_uri,
                "HNAP_AUTH": self._hnap_auth(action),
            },
        )

        try:
            response = json.loads(response.content.strip())
            return response[action + "Response"]

        except json.JSONDecodeError as exc:
            raise MotoError("Unable to decode JSON response.") from exc

        except KeyError as exc:
            raise MotoError("No response from modem.") from exc

    def _do_actions(self, *actions):
        return self._do_action("GetMultipleHNAPs", {action: "" for action in actions})
