import os
import subprocess
from celery import Celery, current_task
import tasks_config
import requests
import urllib.request
import glob
import json

#si = subprocess.STARTUPINFO()
#si.dwFlags = subprocess.STARTF_USESHOWWINDOW
#si.wShowWindow = subprocess.SW_HIDE

proc = subprocess.Popen( [tasks_config.ETPATH+'et.exe', '+set fs_game etpro'] , cwd = tasks_config.ETPATH, shell=True, stdin=subprocess.PIPE, bufsize=1000)
# proc = subprocess.Popen(...)
try:
    outs, errs = proc.communicate(input=b'quit', timeout=5)
    print(outs)
    print(errs)
except subprocess.TimeoutExpired:
    # print(proc.communicate(timeout=5))
    proc.poll()
    #proc.kill()
    outs, errs = proc.communicate()
    print(outs)
    print(errs)
