#!/bin/bash

# Add the following line to /etc/rc.local right before exit 0
# su pi -c 'sh /home/pi/Desktop/dimensiometer/Software/backend/startJupyter.sh'

source /home/pi/.profile
workon volumeter2
jupyter notebook --notebook-dir=/home/pi/Desktop/dimensiometer/Software

