import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD

GPIO.setup(27, GPIO.OUT)           # set GPIO as an output
GPIO.output(27, 1)         # set GPIO to 1/GPIO.HIGH/True
#GPIO.cleanup(27)