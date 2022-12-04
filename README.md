# What is this?

My internet connection is very flaky.  Comcast support is less helpful if you own your own modem.  The modem's interface sucks and doesn't retain logs, so I wrote all this to pull logs down from the modem's crappy soap interface and slice through the logs and connection info to see what's really happening.

[![CI](https://github.com/uoodsq/moto/actions/workflows/ci.yml/badge.svg)](https://github.com/uoodsq/moto/actions/workflows/ci.yml)

# Setup

Set up a Python virtualenv and install the requirements.

```shell
python -m venv venv
source venv/bin/activate  # or whatever
pip install -r requirements.txt
```

If you want to persist reads in InfluxDB, have that running somewhere.

# Usage

Activate the virtualenv and run `python -m moto --help` for usage.

By default, will communicate with your modem at `192.168.100.1` with the default login creds of `admin:motorola`.  If you've change the password, or your modem is available elsewhere, set these environment variables:

- `MOTO_HOSTNAME`
- `MOTO_USERNAME`
- `MOTO_PASSWORD`

If you're using InfluxDB (v2), you need to set these variables as well:

- `INFLUXDB_URL` including protocol and port (e.g. `http://influx:8086`)
- `INFLUXDB_TOKEN` should be scoped with read/write access to the desired bucket
- `INFLUXDB_ORG`
- `INFLUXDB_BUCKET`

# Notes

Recently, my modem has started redirecting from unencrypted HTTP to HTTPS secured with a self-signed cert.  Because of this, I disabled certificate verification in the Python script that pulls stats and logs from the modem.  Use this at your own risk!
