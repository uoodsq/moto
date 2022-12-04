"""
Contains classes related to the representation of logs stored on the modem.
"""
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, Self

from dateutil.parser import parse as parse_datetime
from dateutil.tz import gettz
from influxdb_client import Point


@dataclass
class ModemLog:
    """
    A parsed log entry from the modem.
    """

    timestamp: datetime
    level: str
    message: str

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def to_point(self) -> Point:
        """
        Convert this object to an InfluxDB Point.
        """
        return (
            Point("log")
            .time(self.timestamp)
            .tag("level", self.level)
            .field("message", self.message)
        )

    @classmethod
    def from_response(cls, response: str) -> Generator[Self, None, None]:
        """
        Parse a raw log string into a generator of ModemLog objects.
        """
        for line in response.split("}-{"):
            yield cls.from_line(line)

    @classmethod
    def from_line(cls, line: str) -> Self:
        """
        Parse a single log line into a ModemLog object.
        """
        timestamp_str, line = line.split("\n", 1)
        timestamp = parse_datetime(
            timestamp_str.replace("^", " "),
            tzinfo=gettz(os.getenv("TZ", "UTC")),
        )

        level, line = line.lstrip("^").split("^", 1)

        return cls(timestamp, level, line)
