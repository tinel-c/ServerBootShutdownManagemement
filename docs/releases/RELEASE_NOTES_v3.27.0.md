# v3.27.0 (2026-11-22) - SMS voice call and five-call alarm

**Date:** 2026-11-22  
**Author:** Constantin Bogza

## Summary

The LilyGo SMS gateway can place a voice call. The dashboard dials the number in the phone field once, or rings it five times and hangs up as an alarm.

## Changes

- Firmware **1.1.5** accepts `sms/gateway/command/call`. `call` stays connected until `hangup` or 60 seconds. `alarm` rings about 15 seconds, hangs up, waits 4 seconds, and repeats until five calls are done. Hang up cancels the sequence. Progress is published on `sms/gateway/call/status`.
- Outgoing SMS waits while a call is active so the modem is not interrupted mid-ring.
- The SMS page at `/dashboard/page7` shows a one-row status strip and, beside the message, the phone number, Send, Call, Hang up, and Alarm · 5 calls.

## Deploy

The gateway at `192.168.2.60` is already on 1.1.5, and the dashboard buttons are already on the live Node-RED page. Installed PCs take `client-v3.27.0.zip` on the next update check. The Windows client behavior is unchanged from 3.26.4.
