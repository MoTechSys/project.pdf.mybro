#!/usr/bin/env python3
"""Small native GUI driver for the isolated Packet Tracer validation session.
Screenshots are original pixels; OCR copies are diagnostic only, never proof alone.
No Cisco account credentials or authentication cookies are read by this module.
"""
import os
import re
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
from PIL import ImageGrab, ImageOps
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.git/pt_runtime'
ENV=os.environ|{'DISPLAY':'127.0.0.1:100','LD_LIBRARY_PATH':str(RUNTIME/'usr/lib/x86_64-linux-gnu'),'OMP_THREAD_LIMIT':'1'}
XD=str(RUNTIME/'usr/bin/xdotool')

def x(*args):
 return subprocess.check_output([XD,*map(str,args)],env=ENV,text=True).strip()

def main_window():
 for wid in x('search','--onlyvisible','--class','PacketTracer').split():
  title=x('getwindowname',wid)
  if title.startswith('Cisco Packet Tracer') and 'Login' not in title:
   return wid
 raise RuntimeError('No logged-in native Packet Tracer window found')

def foreground():
 w=main_window();x('windowraise',w,'windowfocus',w);return w

def capture(name='current',crop=(625,215,1310,875)):
 image=ImageGrab.grab(xdisplay=ENV['DISPLAY'])
 image.save(RUNTIME/(name+'.png'))
 clipped=image.crop(crop)
 clean=ImageOps.autocontrast(ImageOps.grayscale(clipped)).resize((clipped.width*2,clipped.height*2))
 clean.save(RUNTIME/(name+'_ocr.png'))
 return subprocess.check_output(['tesseract',str(RUNTIME/(name+'_ocr.png')),'stdout','--psm','6'],env=ENV,stderr=subprocess.DEVNULL,text=True)

def device(name,kind='router'):
 root=ET.parse(ROOT/'pt/university.xml').getroot()
 d=next(d for d in root.findall('NETWORK/DEVICES/DEVICE') if d.findtext('ENGINE/NAME')==name)
 px=float(d.findtext('WORKSPACE/LOGICAL/X'));py=float(d.findtext('WORKSPACE/LOGICAL/Y'))
 existing=[wid for wid in x('search','--class','PacketTracer').split() if x('getwindowname',wid)==name]
 if existing:
  x('windowmap',existing[0],'windowraise',existing[0],'windowfocus',existing[0])
 else:
  foreground();x('mousemove',int(px),int(py+130),'click',1)
 time.sleep(1.2)
 for _ in range(2):
  x('mousemove',779 if kind=='pc' else 768,225,'click',1);time.sleep(.6)

def send(command,wait=.6):
 x('type','--clearmodifiers','--delay',6,command);x('key','Return');time.sleep(wait)

def command_focus():
 x('mousemove',920,500,'click',1)

def dismiss_pager():
 x('key','q');time.sleep(.1)

def router(name):
 device(name)
 text=capture('router_tab')
 if 'IOS Command Line Interface' not in text:
  raise RuntimeError('CLI not ready; do not click the physical device power control')
 command_focus();x('key','Return');time.sleep(.3)
 text=capture('router_login')
 if text.rfind('Username:') > text.rfind('Password:'):
  send('netadmin');send('LabOnly26Admin9')
 if name.startswith('ACC-'):
  text=capture('access_login')
  if '>' in text[-250:] and '#' not in text[-250:]: send('enable');send('LabOnly26Enable9')

def pc(name):
 device(name,'pc')
 text=capture('pc_tab')
 if 'Command Prompt' not in text or 'Cisco Packet Tracer PC' not in text:
  x('mousemove',1280,260,'click',1);time.sleep(.7)
  x('mousemove',1080,285,'click',1);time.sleep(.7)
  text=capture('pc_open')
  if 'Cisco Packet Tracer PC' not in text:
   raise RuntimeError('PC command prompt not visible; no commands sent')
 command_focus()


def wait_prompt(evidence,timeout=150):
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  text=capture(evidence,crop=(637,270,1285,835))
  clean=text.strip().rstrip('|').strip()
  if '--More--' in clean[-150:]:
   x('key','space');time.sleep(.3);continue
  last=clean.splitlines()[-1].strip() if clean else ''
  if len(last)<80 and last.endswith(('#','>')):
   return text
  time.sleep(1)
 raise TimeoutError('No clean console prompt; inspect '+evidence+'.png')


def pc_command(name,command,evidence,timeout=150):
 pc(name);wait_prompt(evidence+'_ready',timeout)
 send(command)
 return wait_prompt(evidence,timeout)

def pc_browser(name,url):
 device(name,'pc');x('mousemove',1280,260,'click',1);time.sleep(.3)
 x('mousemove',1200,285,'click',1);time.sleep(1)
 # Browser address bar in the standard 700x680 device dialog.
 x('mousemove',870,282,'click',1,'key','ctrl+a');send(url,1)
 x('mousemove',1164,282,'click',1)

def fastforward(count=2):
 # Native device dialogs otherwise intercept the keyboard accelerator.
 # Coordinates require the 1800x1000 main window used by this driver.
 w=main_window()
 for wid in x('search','--onlyvisible','--class','PacketTracer').split():
  if wid!=w:x('windowunmap',wid)
 x('windowraise',w,'windowfocus',w)
 for _ in range(count):
  x('mousemove',145,870,'click',1);time.sleep(3)


def save_snapshot():
 foreground();x('key','ctrl+s');time.sleep(1)
