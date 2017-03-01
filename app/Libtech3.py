import subprocess
import sys
import os

def cut(bin_path,input,out,start,end,type,pov):
  subprocess.call(
    [bin_path, 'cut', input, out, str(start),
     str(end), str(type), str(pov)])
  if os.stat(out).st_size == 0:
      raise Exception("Cutted demo is empty, probably wrong start-end time interval")