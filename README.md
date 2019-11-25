# Installation instructions
- Install newest Rasbian Buster Lite  to the Micro SD Card
https://www.raspberrypi.org/downloads/raspbian/

- Create an empty file called ssh to the root of the SD card
```
cd PATH_TO_SDCARD_ROOT
touch ssh
```

- ssh to the pi
```
ssh pi@volumeter.local 
```
- Change the password
```
passwd
raspberry
volumeter
volumeter
```
- Upgrade packages
```
sudo apt update
sudo apt upgrade
sudo apt install python3-pip git libatlas-base-dev
```
- Enable w1 temperature sensor
```
echo "dtoverlay=w1–gpio" | sudo tee -a /boot/config.txt
sudo reboot
sudo modprobe w1-therm
```
- Install python dependencies
```
sudo pip3 install virtualenv virtualenvwrapper
echo "# virtualenv and virtualenvwrapper" >> ~/.profile
echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.profile
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.profile
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.profile
source ~/.profile
```
- Create a python virtualenv
```
mkvirtualenv volumeter -p python3
workon volumeter
```
- Clone the git repository
```
cd ~
git clone https://version.aalto.fi/gitlab/pirttij1/dimensiometer.git
cd dimensiometer
pip install -r requirements.txt
```
- Configuring jupyter
```
jupyter notebook --generate-config
jupyter notebook password
volumeter
volumeter
```
- Edit jupyter_notebook_config.py
```
sudo nano /home/pi/.jupyter/jupyter_notebook_config.py
```
Change:
```
#c.NotebookApp.ip = 'localhost'
```
To:
```
c.NotebookApp.ip = ''
```
- Enable jupyter extensions
```
jupyter contrib nbextension install --user
jupyter nbextension enable --py widgetsnbextension --sys-prefix
jupyter serverextension enable --py nbzip --sys-prefix
jupyter serverextension enable --py nbzip --sys-prefix
```
- Start jupyter on boot
Make a file /etc/systemd/system/volumeter.service
```
sudo nano /etc/systemd/system/volumeter.service
```
Add the following to the file:
```
[Unit]
Description=Volumeter Jupyter Notebook Server
[Service]
Type=simple
PIDFile=/run/volumeter.pid
ExecStart=/home/pi/dimensiometer/startJupyter.sh
User=pi
WorkingDirectory=/home/pi/dimensiometer
[Install]
WantedBy=multi-user.target
```
- Run the commands
```
sudo systemctl enable volumeter.service
sudo systemctl daemon-reload
sudo systemctl restart volumeter.service
```