# what is this?

my internet connection flaked out.  comcast support is less helpful if you own your own modem.  the modem's interface sucks and doesn't retain logs, so i wrote all this to pull logs down from the modem's crappy soap interface and slice through the logs and connection info to see what's really happening.

if you have a motorola mb8600 and [jq](https://stedolan.github.io/jq/) and a crappy upstream connection to diagnose, boy howdy is this repo for you!

[i have a problem](https://twitter.com/uoodsq/status/1172004368553598977)

# Setup

ya need python.  probably in a virtualenv.  install the requirements:

```shell
python -m venv venv
source venv/bin/activate  # or whatever
pip install -r requirements.txt
```