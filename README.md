# what is this?

my internet connection flaked out.  comcast support is less helpful if you own your own modem.  the modem's interface sucks and doesn't retain logs, so i wrote all this to pull logs down from the modem's crappy soap interface and slice through the logs and connection info to see what's really happening.

if you have a motorola mb8600 and [jq](https://stedolan.github.io/jq/) and a crappy upstream connection to diagnose, boy howdy is this repo for you!

# Setup

ya need python.  probably in a virtualenv.  install the requirements:

```shell
python -m venv venv
source venv/bin/activate  # or whatever
pip install -r requirements.txt
```

# Notes

Recently, my modem has started redirecting from unencrypted HTTP to HTTPS secured with a self-signed cert.  Because of this, I disabled certificate verification in the Python script that pulls stats and logs from the modem.  Use this at your own risk!
