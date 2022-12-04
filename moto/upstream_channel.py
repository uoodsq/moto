"""
Contains classes related to the representation of upstream channels.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Generator, Self

from influxdb_client import Point


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

    def to_point(self) -> Point:
        """
        Convert this object to an InfluxDB Point.
        """
        timestamp = datetime.now(timezone.utc)

        return (
            Point("upstream")
            .time(timestamp)
            .tag("channel", str(self.channel))
            .tag("channel_id", str(self.channel_id))
            .tag("lock_status", self.lock_status)
            .tag("channel_type", self.channel_type)
            .field("symbol_rate", self.symbol_rate)
            .field("frequency", self.frequency)
            .field("power", self.power)
        )

    @classmethod
    def from_response(cls, response: str) -> Generator[Self, None, None]:
        """
        Parse the upstream channels string into a generator of upstream channel objects.
        """
        for line in response.split("|+|"):
            yield cls.from_line(line)

    @classmethod
    def from_line(cls, line: str) -> Self:
        """
        Parse an individual upstream channel string into a upstream channel object.
        """
        channel, line = line.split("^", 1)
        channel = int(channel)
        lock_status, line = line.split("^", 1)
        channel_type, line = line.split("^", 1)
        channel_id, line = line.split("^", 1)
        channel_id = int(channel_id)
        symbol_rate, line = line.split("^", 1)
        symbol_rate = Decimal(symbol_rate)
        frequency, line = line.split("^", 1)
        frequency = Decimal(frequency)
        power, line = line.split("^", 1)
        power = Decimal(power.rstrip("^"))

        return cls(
            channel,
            lock_status,
            channel_type,
            channel_id,
            symbol_rate,
            frequency,
            power,
        )
