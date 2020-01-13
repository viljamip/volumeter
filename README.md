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
ssh pi@IP_ADDRESS_OF_THE_PI
```
- Change the password
```
passwd
raspberry
volumeter
volumeter
```
- Change the timezone
```
sudo raspi-config
```

> Localisation options

> Change Timezone

> Europe

> Helsinki

- Change hostname
```
sudo nano /etc/hostname
```
> Change from **raspberrypi** to **volumeter**

- Upgrade and install packages
```
sudo apt update
sudo apt upgrade
sudo apt install python3-pip git libatlas-base-dev build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev libxml2-dev libxslt1-dev -y

- Install python 3.8.0
```
wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tar.xz
tar xf Python-3.8.0.tar.xz
cd Python-3.8.0
./configure
make -j 4
sudo make altinstall
```

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
pip install git+https://github.com/ryanlovett/jupyter-tree-download.git
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
-Extend the life of the Micro SD Card
```
cd ~
git clone https://github.com/azlux/log2ram.git
cd log2ram
chmod +x install.sh
sudo ./install.sh
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo update-rc.d dphys-swapfile remove
```