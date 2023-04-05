import os
import time
import RPi.GPIO as GPIO
# from luma.core import lib
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import Image, ImageFont

SCNTYPE = 1  # 1= OLED #2 = TERMINAL MODE BETA TESTS VERSION

# Load default font.
font = ImageFont.load("fonts/Tamsyn6x12r.pil")

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = 128
height = 64
image = Image.new("1", (width, height))
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
line1 = top
line2 = top + 8
line3 = top + 16
line4 = top + 25
line5 = top + 34
line6 = top + 43
line7 = top + 52
brightness = 255  # Max
file = ""
# Move left to right keeping track of the current x position for drawing shapes.
x = 0
RST = 25
CS = 8
DC = 24

# GPIO define and OLED configuration
RST_PIN = 25  # waveshare settings
CS_PIN = 8  # waveshare settings
DC_PIN = 24  # waveshare settings
KEY_UP_PIN = 6  # stick up
KEY_DOWN_PIN = 19  # stick down
KEY_LEFT_PIN = 5  # 5  #sitck left // go back
KEY_RIGHT_PIN = 26  # stick right // go in // validate
KEY_PRESS_PIN = 13  # stick center button
KEY1_PIN = 21  # key 1 // up
KEY2_PIN = 20  # 20 #key 2 // cancel/goback
KEY3_PIN = 16  # key 3 // down
USER_I2C = 0  # set to 1 if your oled is I2C or  0 if use SPI interface
# init GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_PRESS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
screensaver = 0
# SPI
# serial = spi(device=0, port=0, bus_speed_hz = 8000000, transfer_size = 4096, gpio_DC = 24, gpio_RST = 25)
if SCNTYPE == 1:
    if USER_I2C == 1:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RST, GPIO.OUT)
        GPIO.output(RST, GPIO.HIGH)
        serial = i2c(port=1, address=0x3C)
    else:
        serial = spi(
            device=0,
            port=0,
            bus_speed_hz=8000000,
            transfer_size=4096,
            gpio_DC=24,
            gpio_RST=25,
        )
if SCNTYPE == 1:
    device = sh1106(serial, rotate=2)  # sh1106

def msg(msg, t):
    text("", "", "", str(msg), "", "", "")
    time.sleep(t)


def text(l1, l2, l3, l4, l5, l6, l7):
    # simple routine to display 7 lines of text
    if SCNTYPE == 1:
        with canvas(device) as draw:
            draw.text((0, line1), l1, font=font, fill=255)
            draw.text((0, line2), l2, font=font, fill=255)
            draw.text((0, line3), l3, font=font, fill=255)
            draw.text((0, line4), l4, font=font, fill=255)
            draw.text((0, line5), l5, font=font, fill=255)
            draw.text((0, line6), l6, font=font, fill=255)
            draw.text((0, line7), l7, font=font, fill=255)
    if SCNTYPE == 2:
        os.system("clear")
        print(l1)
        print(l2)
        print(l3)
        print(l4)
        print(l5)
        print(l6)
        print(l7)

def error():
    text("", "", "", "      INTERNAL ERROR", "", "", "")
    time.sleep(5)

def errorNew(error1, error2):
    text("", "", error1, error2, "", "", "")
    time.sleep(5)

def setContrast():
    contrast = brightness
    # set contrast 0 to 255
    if SCNTYPE == 1:
        while GPIO.input(KEY_LEFT_PIN):
            # loop until press left to quit
            with canvas(device) as draw:
                if GPIO.input(KEY_UP_PIN):  # button is released
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=0
                    )  # Up
                else:  # button is pressed:
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                    )  # Up filled
                    contrast = contrast + 5
                    if contrast > 255:
                        contrast = 255

                if GPIO.input(KEY_DOWN_PIN):  # button is released
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=0
                    )  # down
                else:  # button is pressed:
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=1
                    )  # down filled
                    contrast = contrast - 5
                    if contrast < 0:
                        contrast = 0
                device.contrast(contrast)
                draw.text((54, line4), "Value : " + str(contrast), font=font, fill=255)
    return contrast
