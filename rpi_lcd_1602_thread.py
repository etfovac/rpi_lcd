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


import psutil
import signal
import threading
from pynput import keyboard
import sys
import os
sys.path.append(os.path.abspath(".."))
import config.printout_info as cpi
import config.printout_format as cpf


def lcd_setup(lcd_columns = 16,lcd_rows = 2):
    # Raspberry Pi Pin Config:
    lcd_rs = digitalio.DigitalInOut(board.D26)
    lcd_en = digitalio.DigitalInOut(board.D19)
    lcd_d7 = digitalio.DigitalInOut(board.D13)
    lcd_d6 = digitalio.DigitalInOut(board.D6)
    lcd_d5 = digitalio.DigitalInOut(board.D5)
    lcd_d4 = digitalio.DigitalInOut(board.D22)
    lcd_backlight = digitalio.DigitalInOut(board.D27)
    # a NPN transistor's Base switches the LED backlight on/off
       
    # Init lcd class obj
    lcd = characterlcd.Character_LCD_Mono(
        lcd_rs, lcd_en,
        lcd_d4, lcd_d5, lcd_d6, lcd_d7,
        lcd_columns, lcd_rows, lcd_backlight
    )
    lcd.text_direction = lcd.LEFT_TO_RIGHT
    lcd.backlight = True
    lcd.clear()
    lcd.blink = True
    lcd_msg(lcd,"<Setup>...")
    lcd.cursor = True
    msg_list = cpi.lcd_msg_list(lcd_columns, lcd_rows)
    return lcd, msg_list

def lcd_msg(lcd,msg_str):
    lcd.clear()
    sleep(0.1)
    lcd.message = msg_str
    print(lcd.message)

def lcd_printout(lcd,msg_list,delay):
    #print(msg_list)
    try:
        for msg in msg_list:
            lcd_msg(lcd,msg)
            sleep(delay)
    except KeyboardInterrupt: 
        print('<CTRL-C> Printout cancelled. Press CTRL-C to stop execution.')

def lcd_printout_timeout(lcd,msg_list,event,timeout_sec):
    # Triggered on event timeout
    cntr=0
    while not event.isSet():
        cntr+=cntr
        #print(cntr) #=0 => e.wait works
        event_is_set = event.wait(timeout_sec)
        if event_is_set:
            lcd_printout(lcd,msg_list,1.5)
            event.clear() # clear isSet flag in event
        else:
            lcd_msg(lcd,cpf.msg_form(cpi.lcd_timestamp()[0:2]))
            
def lcd_printout_timeout2(lcd,msg_list,event,timeout_sec):
    # Triggered on event timeout
    while not event.isSet():
        event_is_set = event.wait(timeout_sec)
        if not(event_is_set): # periodic remainder
            lcd_printout(lcd,msg_list,3)

lcd_event_print = threading.Event()
lcd_event_print2 = threading.Event() # not used

def on_press(key):
    global lcd_event_print # couldn't add param to this callback
    # Keyboard interupt triggers thread event:
    if key == keyboard.Key.page_down: lcd_event_print.set()

#     try:
#         print('alphanumeric key {0} pressed'.format(key.char))
#     except AttributeError:
#         print('special key {0} pressed'.format(key))

def on_release(key):
    if key == keyboard.Key.esc:
        print('{0} released - Stopping the keyboard listener'.format(key))
        return False
        
def main():
    
    def interrupt_signal_handler(signum, frame):
        print('Interrupt signal ' + str(signum) +
              ' on line ' + str(frame.f_lineno) +
              ' in ' + frame.f_code.co_filename)
        listener.stop()
        lcd.backlight = False # Turns off the LED backlight
        sys.exit(0)
    
    [lcd,msg_lists] = lcd_setup()
    
    #lcd_thread = threading.Thread(target=lcd_printout, args=())
    #lcd_thread.start()
    timeout_sec = [1,6]
    lcd_thread = threading.Thread(name='non-blocking',
                                       target = lcd_printout_timeout,
                                       args = (lcd,msg_lists[0],lcd_event_print,timeout_sec[0]))
    lcd_thread2 = threading.Thread(name='non-blocking',
                                       target = lcd_printout_timeout2,
                                       args = (lcd,msg_lists[1],lcd_event_print2,timeout_sec[1]))
    lcd_thread.start()
    lcd_thread2.start()
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.wait()
    
    signal.signal(signal.SIGINT, interrupt_signal_handler) #Terminal interrupt signal
    signal.pause()
    
if __name__ == "__main__":
    main()   