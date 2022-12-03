"""
Wrappers around InfluxDBClient for this library's purposes.
"""
import os
from typing import Protocol

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteApi


class Pointable(Protocol):  # pylint: disable=too-few-public-methods
    """
    An object that can be converted to an InfluxDB Point.
    """

    def to_point(self) -> Point:
        """
        Convert this object to an InfluxDB Point.
        """


class InfluxClient:  # pylint: disable=too-few-public-methods
    """
    A client for communicating with InfluxDB.
    """

    _url: str
    _token: str
    _org: str
    _bucket: str

    _client: InfluxDBClient
    _write_api: WriteApi

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        org: str | None = None,
        bucket: str | None = None,
    ):
        self._url = url or os.environ.get("INFLUXDB_URL", "http://localhost:8086")
        self._token = token or os.environ["INFLUXDB_TOKEN"]
        self._org = org or os.environ["INFLUXDB_ORG"]
        self._bucket = bucket or os.environ["INFLUXDB_BUCKET"]

        self._client = InfluxDBClient(
            url=self._url,
            token=self._token,
            org=self._org,
        )

        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def ingest(self, pointable: Pointable):
        """
        Ingest a pointable object into InfluxDB.
        """
        point = pointable.to_point()

        self._write_api.write(self._bucket, self._org, point)
