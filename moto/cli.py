"""
Command line interface.
"""
from rich.progress import Progress
from rich.table import Table
from typer import Typer

from .influx_client import InfluxClient
from .moto_client import MotoClient

app = Typer()


def _login(moto, progress: Progress):
    task = progress.add_task("Logging in...", total=None)
    moto.login()
    progress.update(task, total=1, completed=1)


def _get_logs(moto, progress):
    task = progress.add_task("Downloading logs...", total=None)
    logs = list(moto.get_logs())
    progress.update(task, total=1, completed=1)

    return logs


def _ingest_logs(logs, influx, progress):
    task = progress.add_task("Ingesting logs...", total=len(logs))
    for log in logs:
        influx.ingest_log(log)
        progress.update(task, advance=1)


def _get_downstream_channels(moto, progress):
    task = progress.add_task("Downloading downstream channels...", total=None)
    channels = list(moto.get_downstream_channels())
    progress.update(task, completed=True)

    return channels


def _ingest_downstream_channels(channels, influx, progress):
    task = progress.add_task("Ingesting downstream channels...", total=len(channels))
    for channel in channels:
        influx.ingest_downstream_channel(channel)
        progress.update(task, advance=1)


def _get_upstream_channels(moto, progress):
    task = progress.add_task("Downloading upstream channels...", total=None)
    channels = list(moto.get_upstream_channels())
    progress.update(task, completed=True)

    return channels


def _ingest_upstream_channels(channels, influx, progress):
    task = progress.add_task("Ingesting upstream channels...", total=len(channels))
    for channel in channels:
        influx.ingest_upstream_channel(channel)
        progress.update(task, advance=1)


def _print_downstream_channels(channels, progress):
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
        title="Downstream Channels",
    )

    for channel in sorted(channels):
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

    progress.console.print(table)


def _print_upstream_channels(channels, progress):
    table = Table(
        "Channel",
        "Lock Status",
        "Channel Type",
        "Channel ID",
        "Symbol Rate",
        "Frequency",
        "Power",
        title="Upstream Channels",
    )

    for channel in sorted(channels):
        table.add_row(
            str(channel.channel),
            channel.lock_status,
            channel.channel_type,
            str(channel.channel_id),
            str(channel.symbol_rate),
            str(channel.frequency),
            str(channel.power),
        )

    progress.console.print(table)


@app.command()
def read():
    influx = InfluxClient()
    moto = MotoClient()

    with Progress() as progress:
        _login(moto, progress)

        logs = _get_logs(moto, progress)
        _ingest_logs(logs, influx, progress)

        channels = _get_downstream_channels(moto, progress)
        _ingest_downstream_channels(channels, influx, progress)

        channels = _get_upstream_channels(moto, progress)
        _ingest_upstream_channels(channels, influx, progress)


@app.command()
def dump():
    moto = MotoClient()

    with Progress() as progress:
        _login(moto, progress)

        channels = _get_downstream_channels(moto, progress)
        _print_downstream_channels(channels, progress)

        channels = _get_upstream_channels(moto, progress)
        _print_upstream_channels(channels, progress)
