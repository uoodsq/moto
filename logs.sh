#!/usr/bin/env bash
cat ~/log/modem.log | jq ".data.GetMotoStatusLogResponse.MotoStatusLogList" | ./logs.py $@