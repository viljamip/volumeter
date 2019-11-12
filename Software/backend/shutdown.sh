#!/bin/bash
jupyter notebook stop 8888

while pgrep jupyter; do
	sleep 1
done

sudo shutdown -P now

