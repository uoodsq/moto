"""
Contains classes related to the representation of downstream channels.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Generator, Self

from influxdb_client import Point


@dataclass
class DownstreamChannel:  # pylint: disable=too-many-instance-attributes
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

    def to_point(self) -> Point:
        """
        Convert this object to an InfluxDB Point.
        """
        timestamp = datetime.now()

        return (
            Point("downstream")
            .time(timestamp)
            .tag("channel", str(self.channel))
            .tag("channel_id", str(self.channel_id))
            .tag("lock_status", self.lock_status)
            .tag("modulation", self.modulation)
            .field("frequency", self.frequency)
            .field("power", self.power)
            .field("snr", self.snr)
            .field("corrected", self.corrected)
            .field("uncorrected", self.uncorrected)
        )

    @classmethod
    def from_response(cls, response: str) -> Generator[Self, None, None]:
        """
        Parse the downstream channels string into a generator of downstream channel objects.
        """
        for line in response.split("|+|"):
            yield cls.from_line(line)

    @classmethod
    def from_line(cls, line: str) -> Self:
        """
        Parse an individual downstream channel string into a downstream channel object.
        """
        channel, line = line.split("^", 1)
        channel = int(channel)
        lock_status, line = line.split("^", 1)
        modulation, line = line.split("^", 1)
        channel_id, line = line.split("^", 1)
        channel_id = int(channel_id)
        frequency, line = line.split("^", 1)
        frequency = Decimal(frequency)
        power, line = line.split("^", 1)
        power = Decimal(power)
        snr, line = line.split("^", 1)
        snr = Decimal(snr)
        corrected, line = line.split("^", 1)
        corrected = int(corrected)
        uncorrected, line = line.split("^", 1)
        uncorrected = int(uncorrected.rstrip("^"))

        return cls(
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
