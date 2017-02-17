import subprocess

def cut(bin_path,input,out,start,end,type,pov):
  subprocess.call(
    [bin_path, 'cut', input, out, str(start),
     str(end), str(type), str(pov)])