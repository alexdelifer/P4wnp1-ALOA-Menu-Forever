import subprocess
from library import display
import time

installDir = "/root/DeliMenu"
lootDir = "/usr/local/P4wnP1/www/loot/DeliMenu"

def execCmd(cmd: str, skipError=False):
    result = None
    try:
        result = subprocess.check_output(cmd, shell=True)
        result = result.strip().decode("utf-8")
    except subprocess.CalledProcessError:
        result = -1

    # if we failed to run the command
    if result == -1 and skipError is not True:
        display.errorNew("error when running", cmd)
        time.sleep(3)
        return ()
    return str(result)

def execCmdInBackground(cmd: str):
    result = None
    try:
        result = subprocess.Popen(cmd.split())
    except subprocess.CalledProcessError:
        result = -1

    # if we failed to run the command
    if result == -1:
        display.errorNew("error when running", cmd)
        time.sleep(3)
        return None
    return result

def execCmdNoStr(cmd: str):
    try:
        return subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        return -1