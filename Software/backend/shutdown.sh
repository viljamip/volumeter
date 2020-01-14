#!/bin/bash
sudo kill $(pgrep jupyter)
sleep 10
sudo shutdown -P now

