from library import display, system
import time
import os
from PIL import Image
import RPi.GPIO as GPIO

def splash():
    img_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../images", "bootdefcon.bmp")
    )
    splash = (
        Image.open(img_path)
        .transform(
            (display.device.width, display.device.height),
            Image.AFFINE,
            (1, 0, 0, 0, 1, 0),
            Image.BILINEAR,
        )
        .convert(display.device.mode)
    )
    display.device.display(splash)
    time.sleep(3)  # 3 sec splash boot screen

def fileSelect(path, ext):
    cmd = "ls -F --format=single-column  " + path + "*" + ext
    result = system.execCmd(cmd)
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
    while GPIO.input(display.KEY_LEFT_PIN):
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
        if not GPIO.input(display.KEY_UP_PIN):
            cur = cur - 1
            if cur < 0:
                cur = 0
        if not GPIO.input(display.KEY_DOWN_PIN):
            cur = cur + 1
            if cur > maximum - 2:
                cur = maximum - 2
        if not GPIO.input(display.KEY_RIGHT_PIN):
            lastmenu = listattack[cur] + ext
            return lastmenu
        # print(str(cur) + " " + listattack[cur])        #debug
        display.text(
            item[0], item[1], item[2], item[3], item[4], item[5], item[6]
        )
        time.sleep(0.1)
    return ""

def scrollMenu(items: list):
    time.sleep(0.1)
    maximum = len(items)
    currentline = 0
    lines = ["", "", "", "", "", "", ""]
    # while you haven't pushed the back button
    while True:
        # we loop

        # back out
        if not GPIO.input(display.KEY_LEFT_PIN):  # button is released
            print("Left button pressed in scrollMenu")
            time.sleep(0.1)
            return None

        # calculate the start and end index of the displayed items
        start_index = currentline
        end_index = currentline + 7
        if end_index > maximum:
            end_index = maximum
            start_index = maximum - 7
            if start_index < 0:
                start_index = 0

        # populate the lines with the displayed items
        for n in range(start_index, end_index):
            if n == currentline:
                lines[n-start_index] = ">" + items[n]
            else:
                lines[n-start_index] = " " + items[n]

        # controls
        if not GPIO.input(display.KEY_UP_PIN): # button is pressed:
            if not currentline <= 0:
                currentline = currentline - 1
            else:
                currentline = 0

        if not GPIO.input(display.KEY_DOWN_PIN): # button is pressed:
            if not currentline >= maximum - 1:
                currentline = currentline + 1
            else:
                currentline = maximum - 1

        # select item
        if not GPIO.input(display.KEY3_PIN) or not GPIO.input(display.KEY_RIGHT_PIN):  # button is released
            print("selected: " + str(currentline) + " -> " + items[currentline])
            time.sleep(0.2)
            return currentline

        # render display
        display.text(*lines)
        time.sleep(0.1)

def scrollDictMenu(items: dict):
    keylist = list(items.keys())
    key = scrollMenu(keylist)
    if key is not None:
        selection = items[keylist[key]] # systemSettings()
        print(key)
        print(selection)
        return selection
    else:
        return None

def functionalMenu(items: dict):
    time.sleep(0.1)
    selection = None
    selection = scrollDictMenu(items)
    print(selection)
    if selection is not None:
        selection()