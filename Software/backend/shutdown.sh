#!/bin/bash
sudo kill $(pgrep jupyter)

while pgrep jupyter; do
	sleep 1
done

sudo shutdown -P now

