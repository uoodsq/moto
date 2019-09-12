#!/usr/bin/env bash
cat ~/log/modem.log | jq '{ts: .ts, uptime: .data.GetMotoStatusConnectionInfoResponse.MotoConnSystemUpTime}'