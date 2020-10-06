# Display RPi info on a monochromatic character LCD 
# Version:  v1.0
# Author: Nikola Jovanovic
# Date: 04.09.2020.
# Repo: https://github.com/etfovac/rpi_lcd
# SW: Python 3.7.3
# HW: Pi Model 3B  V1.2, LCD 1602 module (HD44780, 5V, Blue backlight, 16 chars, 2 lines)

# https://learn.adafruit.com/character-lcds/python-circuitpython
# https://www.rototron.info/using-an-lcd-display-with-inputs-interrupts-on-raspberry-pi/
# https://www.rototron.info/lcd-display-tutorial-for-raspberry-pi/#downloads
# https://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/
# https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/python-code

import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from time import sleep, strftime
import datetime
import subprocess
import platform
import psutil

lcd_columns = 16
lcd_rows = 2

# Raspberry Pi Pin Config:
lcd_rs = digitalio.DigitalInOut(board.D26)
lcd_en = digitalio.DigitalInOut(board.D19)
lcd_d7 = digitalio.DigitalInOut(board.D13)
lcd_d6 = digitalio.DigitalInOut(board.D6)
lcd_d5 = digitalio.DigitalInOut(board.D5)
lcd_d4 = digitalio.DigitalInOut(board.D22)
#lcd_backlight = digitalio.DigitalInOut(board.D27)
# get a transistor BC547 and use Base to switch on/off the LED backlight

# Initialise the lcd class
lcd = characterlcd.Character_LCD_Mono(
    lcd_rs, lcd_en,
    lcd_d4, lcd_d5, lcd_d6, lcd_d7,
    lcd_columns, lcd_rows #, lcd_backlight
)

# Turn backlight on
#lcd.backlight = True
# Text direction to left to right
lcd.text_direction = lcd.LEFT_TO_RIGHT

def lcd_msg(line1,line2="",form1="",form2=""):
    if type(line1) is tuple:
        line2 = line1[1]
        line1 = line1[0]
    if form1=="": form1="{}"
    if form2=="": form2="{}"
    line1 = form1.format(line1)[:lcd_columns]
    line2 = form2.format(line2)[:lcd_columns]
    msg_form = "{}\n{}"
    msg_str = msg_form.format(line1,line2)
    lcd.clear()
    lcd.message = msg_str
    #print(lcd.message)
    return msg_str

def get_ip():
    # "{} IP address".format(subprocess.getoutput("hostname -I"))
    # iwconfig wlan0 # info iwgetid
    # ethtool eth0 # ethtool -i eth0
    # ifconfig lo
    if psutil.net_if_stats()['wlan0'].isup:
        ip_addr = psutil.net_if_addrs()['wlan0'][0].address
        ip_net = subprocess.getoutput("iwgetid -r")
    elif psutil.net_if_stats()['eth0'].isup:
        ip_addr = psutil.net_if_addrs()['eth0'][0].address
        ip_net = "LAN eth0"
    elif psutil.net_if_stats()['lo'].isup:
        ip_addr = psutil.net_if_addrs()['lo'][0].address #127.0.0.1
        ip_net = "Loopback"
    else:
        ip_addr = "0.0.0.0"
        ip_net = "all net if down"
    return ip_addr, ip_net #tuple

def get_wlan():
    # iwlist wlan0 freq # iwlist wlan0 scan
    # iwlist wlan0 rate # iwlist rate
    # iwgetid --protocol wlan0 -r
    # iwgetid --scheme wlan0 -r
    if psutil.net_if_stats()['wlan0'].isup:
        freq = float(subprocess.getoutput("iwgetid --freq wlan0 -r"))/1e9
        chnl = int(subprocess.getoutput("iwgetid --channel wlan0 -r"))
    else:
        freq = 0
        chnl = 0
    return freq, chnl #tuple

plt_id = platform.uname()
ts_form = "%b %d  %H:%M:%S"
bts = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime(ts_form)
degree = chr(223)

try:
    while 1:
        lcd_msg(plt_id.system,plt_id.node, "OS {}")
        sleep(2)
        lcd_msg(plt_id.release,plt_id.machine, "rel {}", "chip  {}")
        sleep(2)
        lcd_msg(get_ip(), "", "{} IP", "{} ID")
        sleep(2)
        lcd_msg(get_wlan(), "", "CFreq {} GHz", "WLAN Channel {}")
        sleep(3)
        cts = datetime.datetime.now().strftime(ts_form)
        lcd_msg(bts,cts)
        sleep(2)
        # Sep 04  12:32:53
        # Sep 04  15:02:38
        lcd_msg("CPU {} %".format(psutil.cpu_percent()),"CPU {} {}C".format(psutil.sensors_temperatures()['cpu_thermal'][0].current, degree))
        sleep(3)
        lcd_msg(psutil.virtual_memory().percent,psutil.swap_memory().percent,"Virt MEM {} %","Swap MEM {} %")
        sleep(3)
        
except KeyboardInterrupt: 
    print('CTRL-C pressed.  Program exiting...')

finally:
    lcd.clear()
