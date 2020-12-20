# Display RPi info on a monochromatic character LCD
# Version:  v2.0
# Author: Nikola Jovanovic
# Date: 09.12.2020.
# Repo: https://github.com/etfovac/rpi_lcd
# SW: Python 3.7.3
# HW: Pi Model 3B  V1.2, LCD 1602 module (HD44780, 5V, Blue backlight, 
# 16 chars, 2 lines), Bi-Polar NPN Transistor (2N3904 or eq)

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
import datetime
import time
import signal
import threading
from pynput import keyboard
import sys
import os
sys.path.append(os.path.abspath(".."))
import config.printout_info as cpi
import config.printout_format as cpf
import config.time_track as tt

class LCD():
    def __init__(self, lcd_columns=16, lcd_rows=2):
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
        self.LCD = characterlcd.Character_LCD_Mono(
            lcd_rs, lcd_en,
            lcd_d4, lcd_d5, lcd_d6, lcd_d7,
            lcd_columns, lcd_rows, lcd_backlight
        )
        self.LCD.text_direction = self.LCD.LEFT_TO_RIGHT
        self.LCD.backlight = True
        self.LCD.clear()
        self.LCD.blink = True
        self.status = "<Setup>..."
        self.display_single(self.status)
        self.LCD.cursor = True

        self.tt = tt.TimeTrack()
        self.msg_list = cpi.lcd_msg_list(lcd_columns, lcd_rows)  
        #  RPi Infos

        self.printout_threads_setup([1,12])
        self.keyboard_listener_setup()


    def display_single(self, msg):
        """Prints a text message to terminal and LCD.
        LCD is first cleared.
        Args:
            msg (string): string formatted by printout_format.py into 2 rows of 16 chars
        """
        self.LCD.clear()
        time.sleep(0.1)
        self.LCD.message = msg
        print(self.LCD.message)

    def display_multi(self, list_msg, delay):
        """Prints a list of text messages to terminal and LCD.
        LCD is first cleared.
        Args:
            list_msg (string list):  a list of text messages formatted by printout_format.py into 2 rows of 16 chars
            delay (int): thread sleep
        """
        self.LCD.clear()
        time.sleep(0.1)
        for msg in list_msg:
            self.display_single(cpf.msg_form(msg))
            time.sleep(delay)
    
    def display_multi_info(self, ix, delay):
        """Displays RPi information (CPU, RAM, Eth, WLAN, etc)

        Args:
            ix (int):  screen index
            delay (int): thread sleep
        """
        for msg in self.msg_list[ix]:
            self.display_single(msg)
            time.sleep(delay)

    def lcd_print_timeout(self, end_event, event, timeout_sec=[1,12]):
        # Triggered on event timeout >> periodic
        cntr = 0
        while (not event.isSet()) and (not end_event.isSet()):
            cntr += cntr
            # print(cntr) #=0 => e.wait works
            event_is_set = event.wait(timeout_sec[0])
            if end_event.isSet(): break
            if event_is_set:
                # infos[0]
                self.display_multi_info(0,1.5)
                event.clear()  # clear isSet flag in event
            else: # not set >> perform periodic updates
                # timestamps
                self.display_single(cpf.msg_form(self.tt.timestamps()[0:2]))
                # periodic remainder
                if self.tt.timedeltas(timeout_sec[1])[2]:
                    # infos[1] <controls>
                    self.display_multi_info(1,2)
          
    def lcd_print(self, end_event, event_to):
        # Not triggered on event timeout
        while (not event_to.isSet()) and (not end_event.isSet()):
            event_is_set = event_to.wait(0.2)
            if end_event.isSet(): break
            if event_is_set:
               self.display_single(cpf.msg_form(self.status))       
               event_to.clear()

    def printout_threads_setup(self, timeout_sec=[1,12]):
        self.event_print_to1 = threading.Event()
        self.event_end = threading.Event()
        self.event_print = threading.Event()

        self.lcd_thread_p1 = threading.Thread(name='non-blocking P1',
                                    target = self.lcd_print_timeout,
                                    args = (self.event_end, self.event_print_to1,
                                            timeout_sec))
        self.lcd_thread_p2 = threading.Thread(name='non-blocking P2',
                                    target=self.lcd_print,
                                    args=(self.event_end, self.event_print))        

    def on_press(self,key):
        # Keyboard interupt sets thread event:
        if key == keyboard.Key.insert:
            self.event_print_to1.set()

    def on_release(self,key):
        if key == keyboard.Key.esc:
            self.status = cpf.msg_form("<Esc>","No keyboard")
            self.event_print.set()
            return False
        if key == keyboard.Key.end:
            self.end()
            return False
        if key == keyboard.Key.tab:
            self.event_print.set()

    def printout_threads_start(self):
        self.lcd_thread_p1.start()
        self.lcd_thread_p2.start()
        self.status = "Threads..." 

    def keyboard_listener_setup(self):
        self.listener = keyboard.Listener(on_press = self.on_press,
                                          on_release = self.on_release)

    def keyboard_listener_start(self):
        self.listener.start()
        self.listener.wait()

    def end(self):
        self.listener.stop()
        self.event_end.set()  # Send End event to LCD printouts
        self.lcd_thread_p1.join()
        self.lcd_thread_p2.join()
        self.LCD.backlight = False  # Turns off the LED backlight
        sys.exit(0)

        
def main():
    LCD_ref = LCD()
    LCD_ref.printout_threads_start()
    LCD_ref.keyboard_listener_start()
  
if __name__ == "__main__":
    main()   
