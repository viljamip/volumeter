#!/bin/bash
jupyter notebook stop 8888

while prgep jupyter; do
	sleep 1
done

sudo shutdown -P now

