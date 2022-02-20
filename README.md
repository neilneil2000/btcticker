# Cryptocurrency Ticker 
(supports all 7000+ coins/currencies listed on [CoinGecko](https://api.coingecko.com/api/v3/coins/list))

A fork of llvllch/btcticker to work with TFT screen

A Cryptocurrency price ticker that runs as a Python script on a Raspberry Pi connected to an [Adafruit tft display](https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi). The script periodically (every 5 mins by default) takes data from CoinGecko and displays a summary on the screen.

A few minutes work gives you a desk ornament that will tastefully and unobtrusively monitor a coin's journey moonward.

![Action Shot](/images/actionshot/BasicLunar.jpg)


# Getting started

## Prerequisites

(These instructions assume that your Raspberry Pi is already connected to the Internet, happily running `pip` and has `python3` installed)

If you are running the Pi headless, connect to your Raspberry Pi using `ssh`.

Connect to your ticker over ssh and update and install necessary packages 
```
sudo apt-get update
sudo apt-get install -y python3-pip mc git libopenjp2-7
sudo apt-get install -y libatlas-base-dev python3-pil python3-pygame
```

Download PiTFT set up scripts

```
cd ~
sudo pip3 install --upgrade adafruit-python-shell click
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
```

Configure PiTFT (say no to both Console Display and HDMI Mirror questions)

```
sudo python3 adafruit-pitft.py
```

Enable SPI Interface

```
sudo raspi-config nonint do_spi 0
```

Now clone this script

```
cd ~
git clone https://github.com/neilneil2000/btcticker.git
```
Move to the `btcticker` directory, copy the example config to `config.yaml`
```
cd btcticker
cp config_example.yaml config.yaml
```
Install the required Python3 modules
```
sudo python3 -m pip install -r requirements.txt
```

## Autostart
Set Permissions for startup script
```
chmod 777 btcticker.startup.sh
```
Create New SystemCtl Service
```
cat <<EOF | sudo tee /etc/systemd/system/btcticker.service
[Unit]
Description=Bitcoin Ticker
After=network.service

[Service]
Type=simple
KillSignal=SIGHUP
ExecStart=/home/pi/btcticker/btcticker.startup.sh
WorkingDirectory=/home/pi/btcticker/
Restart=always

[Install]
WantedBy=multi-user.target

EOF
```
Enable SystemCtl for our Service
```
sudo systemctl enable btcticker.service
```
## Config.yaml Values

- **display**:
   - **colour**: Display will use glorious technicolour if set to **true** or grayscale if set to **false**
   - **cycle**: switch the display between the listed currencies if set to **true**, display only the first on the list if set to **false**
   - **inverted** :  switches the screen between a white and black background
   - **orientation**: Screen rotation in degrees , can take values **0,90,180,270**
   - **showvolume, showrank**: **true** to include in display, **false** to omit
- **ticker**:
   - **currency**: the coin(s) you would like to display (must be the coingecko id)
   - **fiatcurrency**: currently only uses first one (unless you are cycling with buttons)
   - **sparklinedays**: Number of days of historical data appearing on chart
   - **updatefrequency**: (in seconds), how often to refresh the display
- **buttons**: The below take GPIO pin numbers (BCM) to activate additional functions
   - **invert**: GPIO pin to toggle between black and white backgrounds
   - **nextcrypto**: GPIO pin to skip to next crypto in list
   - **shutdown**: GPIO pin to shutdown device (must hold for 3 seconds)



# Contributing

To contribute, please fork the repository and use a feature branch. Pull requests are welcome.




# Licencing

GNU GENERAL PUBLIC LICENSE Version 3.0
