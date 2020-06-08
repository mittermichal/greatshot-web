"""
Detect when system is idle, globally. That is, the user is not
moving the mouse nor typing anything, in any application (not
just our program).

This is done using the GetLastInputInfo function, which records
keyboard and mouse events in the current session only; note that
this does not include remote users logged in using Terminal Server.

Platform: Windows only.
Requires ctypes; tested with Python 2.5, 2.6, 3.0 and 3.1

(C) 2009 Gabriel A. Genellina
"""

import ctypes, ctypes.wintypes

# http://msdn.microsoft.com/en-us/library/ms646272(VS.85).aspx
# typedef struct tagLASTINPUTINFO {
#     UINT cbSize;
#     DWORD dwTime;
# } LASTINPUTINFO, *PLASTINPUTINFO;

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
      ('cbSize', ctypes.wintypes.UINT),
      ('dwTime', ctypes.wintypes.DWORD),
      ]

PLASTINPUTINFO = ctypes.POINTER(LASTINPUTINFO)

# http://msdn.microsoft.com/en-us/library/ms646302(VS.85).aspx
# BOOL GetLastInputInfo(PLASTINPUTINFO plii);

user32 = ctypes.windll.user32
GetLastInputInfo = user32.GetLastInputInfo
GetLastInputInfo.restype = ctypes.wintypes.BOOL
GetLastInputInfo.argtypes = [PLASTINPUTINFO]

kernel32 = ctypes.windll.kernel32
GetTickCount = kernel32.GetTickCount
Sleep = kernel32.Sleep


#Start a new thread that will poll last input
#set variable for stopping
#while we are not stopping,
#  




import threading

class IdleThread(threading.Thread):
   """
   This class will raise an event every time the system is
   considered Idle.  
   """
   def __init__(self,idleTime,idleEvent,continueEvent):
      self.callback = None
      self.idleTime = idleTime
      self.idleEvent = idleEvent
      self.continueEvent = continueEvent
      threading.Thread.__init__(self)

   def setCallback(self,callback):
      self.callback = callback

   def run(self):
      idle_time_ms = int(self.idleTime*1000)
      liinfo = LASTINPUTINFO()
      liinfo.cbSize = ctypes.sizeof(liinfo)
      while True:
         if not self.continueEvent.isSet():
            break
         if not self.idleEvent.isSet():
            GetLastInputInfo(ctypes.byref(liinfo))
            elapsed = GetTickCount() - liinfo.dwTime
            if elapsed>=idle_time_ms:
               lasttime = None
               self.idleEvent.set()
               if self.callback is not None:
                  self.callback()
            else:
               Sleep(idle_time_ms - elapsed or 1)


class ActiveThread(threading.Thread):
   """
   This class will clear the idle event every time the system is
   considered active. 
   """
   def __init__(self,idleEvent,continueEvent):
      self.callback = None
      self.idleEvent = idleEvent
      self.continueEvent = continueEvent
      threading.Thread.__init__(self)

   def setCallback(self,callback):
      self.callback = callback

   def run(self):
      liinfo = LASTINPUTINFO()
      liinfo.cbSize = ctypes.sizeof(liinfo)
      lasttime = None
      delay = 1 # ms
      maxdelay = int(1*1000)
      while True:
         if not self.continueEvent.isSet():
            break
         if self.idleEvent.isSet():
            GetLastInputInfo(ctypes.byref(liinfo))
            if lasttime is None: lasttime = liinfo.dwTime
            if lasttime != liinfo.dwTime:
               lasttime = None
               self.idleEvent.clear()
               if self.callback is not None:
                  self.callback()
            else:
               delay = min(2*delay, maxdelay)
               Sleep(delay)

class IdleChecker:
   def __init__(self,idle_time):
      self.idleTime = idle_time
      self.idleEvent = threading.Event()
      self.continueEvent = threading.Event()
      self.continueEvent.set()
      self.activeThread = ActiveThread(self.idleEvent, self.continueEvent)
      self.idleThread = IdleThread(self.idleTime,self.idleEvent, self.continueEvent)
      self.idleThread.start()
      self.activeThread.start()

   def __del__(self):
      self.stop()

   def isActive(self):
      return not self.isIdle()

   def isIdle(self):
      return self.idleEvent.isSet()

   def setActiveCallback(self,callback):
      self.activeThread.setCallback(callback)

   def setIdleCallback(self,callback):
      self.idleThread.setCallback(callback)

   def stop(self):
      self.continueEvent.clear()

if __name__ == '__main__':
   def back():
      print("I am back!")

   def gone():
      print("I am gone...")

   idleChecker = IdleChecker(4)
   i = 0
   while True:
      i = i + 1
      print(i)
      Sleep(1000)
      if idleChecker.isIdle(): print("yup... it's idle.")
      idleChecker.setActiveCallback(back)
      idleChecker.setIdleCallback(gone)
      if i == 20:
         break
   idleChecker.stop()
