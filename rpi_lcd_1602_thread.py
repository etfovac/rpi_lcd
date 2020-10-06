# Display RPi info on a monochromatic character LCD 
# Version:  v1.0
# Author: Nikola Jovanovic
# Date: 04.09.2020.
# Repo: https://github.com/etfovac/rpi_lcd
# SW: Python 3.7.3
# HW: Pi Model 3B  V1.2, LCD 1602 module (HD44780, 5V, Blue backlight, 16 chars, 2 lines), Bi-Polar NPN Transistor (2N3904 or eq)

# https://learn.adafruit.com/character-lcds/python-circuitpython
# https://www.mbtechworks.com/projects/drive-an-lcd-16x2-display-with-raspberry-pi.html
# https://www.rototron.info/using-an-lcd-display-with-inputs-interrupts-on-raspberry-pi/
# https://www.rototron.info/lcd-display-tutorial-for-raspberry-pi/#downloads
# https://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/
# https://www.elprocus.com/lcd-16x2-pin-configuration-and-its-working/
# https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/python-code
# https://bogotobogo.com/python/Multithread/python_multithreading_Event_Objects_between_Threads.php
# https://pypi.org/project/pynput/
# https://components101.com/transistors/bc548-npn-transistor

import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from time import sleep, strftime
import datetime
import subprocess
import platform
import psutil
import signal
import sys
import threading
from pynput import keyboard


lcd_columns = 16
lcd_rows = 2

plt_id = platform.uname()
ts_form = "%b %d  %H:%M:%S"
bts = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime(ts_form)
degree = chr(223) # spec. char for °
def lcd_setup():
    global lcd
    # Raspberry Pi Pin Config:
    lcd_rs = digitalio.DigitalInOut(board.D26)
    lcd_en = digitalio.DigitalInOut(board.D19)
    lcd_d7 = digitalio.DigitalInOut(board.D13)
    lcd_d6 = digitalio.DigitalInOut(board.D6)
    lcd_d5 = digitalio.DigitalInOut(board.D5)
    lcd_d4 = digitalio.DigitalInOut(board.D22)
    lcd_backlight = digitalio.DigitalInOut(board.D27)
    # a NPN transistor's Base switches the LED backlight on/off

    # Initialise the lcd class
    lcd = characterlcd.Character_LCD_Mono(
        lcd_rs, lcd_en,
        lcd_d4, lcd_d5, lcd_d6, lcd_d7,
        lcd_columns, lcd_rows, lcd_backlight
    )

    lcd.text_direction = lcd.LEFT_TO_RIGHT
    lcd.backlight = True
    lcd.clear()
    lcd.blink = True
    lcd.message = "Blink!"
    lcd.cursor = True

def lcd_msg(line1,line2="",form1="",form2=""):
    global lcd
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
    print(lcd.message)
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

def lcd_timestamp():
        cts = datetime.datetime.now().strftime(ts_form)
        lcd_msg(bts,cts)
        #sleep(1) # event timeout solves this
        # Sep 04  12:32:53
        # Sep 04  15:02:38

def lcd_printout():
    try:
        lcd_ribbon()
        sleep(1)
        lcd_msg(plt_id.system,plt_id.node, "OS {}")
        sleep(2)
        lcd_msg(plt_id.release,plt_id.machine, "rel {}", "chip  {}")
        sleep(2)
        lcd_msg(get_ip(), "", "{} IP", "{} ID")
        sleep(2)
        lcd_msg(get_wlan(), "", "CFreq {} GHz", "WLAN Channel {}")
        sleep(2)
        #lcd_timestamp()
        #sleep(1)
        lcd_msg("CPU {} %".format(psutil.cpu_percent()),"CPU {} {}C".format(psutil.sensors_temperatures()['cpu_thermal'][0].current, degree))
        sleep(2)
        lcd_msg(psutil.virtual_memory().percent,psutil.swap_memory().percent,"Virt MEM {} %","Swap MEM {} %")
        sleep(2)
        lcd_ribbon()
    except KeyboardInterrupt: 
        print('CTRL-C pressed. Printout cancelled. Press CTRL-C to stop execution.')

def lcd_ribbon():
    lcd_msg(">"*lcd_columns,"<"*lcd_columns)
    
def lcd_printout_timeout(event,timeout_sec):
    cntr=0
    while not event.isSet():
        cntr+=cntr
        #print(cntr) #=0 => e.wait works
        event_is_set = event.wait(timeout_sec)
        if event_is_set:
            lcd_printout()
            event.clear() # clear isSet flag in event
        else:
            lcd_timestamp()

lcd_event_print = threading.Event()

def on_press(key):
    global lcd_event_print # couldn't add param to this callback
    if key == keyboard.Key.page_down: lcd_event_print.set()
#     try:
#         print('alphanumeric key {0} pressed'.format(key.char))
#     except AttributeError:
#         print('special key {0} pressed'.format(key))
def on_release(key):
    
    if key == keyboard.Key.esc:
        # Stop listener
        print('{0} released - Stopping the keyboard listener'.format(key))
        return False
        
def main():
    
    def interrupt_signal_handler(sig, frame):
        print('Program exiting...')
        listener.stop()
        lcd.backlight = False # Turns off the LED backlight
        
        sys.exit(0)
    
    lcd_setup()
    
    #lcd_thread = threading.Thread(target=lcd_printout, args=())
    #lcd_thread.start()
    timeout_sec = 1
    lcd_thread_tout = threading.Thread(name='non-blocking', target=lcd_printout_timeout, args=(lcd_event_print,timeout_sec))
    lcd_thread_tout.start()
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.wait()
    
    signal.signal(signal.SIGINT, interrupt_signal_handler) #Terminal interrupt signal
    signal.pause()
    
if __name__ == "__main__":
    main()   