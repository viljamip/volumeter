#!/bin/bash
source /home/pi/.virtualenvs/volumeter/bin/activate
jupyter notebook --notebook-dir='/home/pi/dimensiometer/Software' --log-level='CRITICAL'

