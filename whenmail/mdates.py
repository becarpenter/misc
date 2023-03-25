#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Email sending plotter. It makes histograms of day and time
when emails were sent to IETF destinations, based on an email
file in MBOX format.
No warranty. Use, copy and modify as you wish, at your own risk.""" 

from tkinter import Tk
from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter.messagebox import showinfo
import matplotlib.pyplot as plot
#And why not import datetime? It's just too abstruse, so I did it the hard way.

class daterec:
    """A complete date record"""
    def __init__(self, day, hour, minute, uday, uhour, umin):
        self.day = day
        self.hour = hour
        self.minute = minute
        self.uday = uday
        self.uhour = uhour
        self.umin = umin

def rf(f):
    """Return a file as a list of strings"""
    file = open(f, "r",encoding='utf-8', errors='replace')
    l = file.readlines()
    file.close()
    return l

def duoval(s):
    """Evaluate two digit string"""
    if s[0] == "0":
        return eval(s[1])
    else:
        return eval(s[0:2])

def before(d):
    """The day before"""
    global daynames
    if not d in daynames:
        return "xxx"
    return daynames[(daynames.index(d)-1)%7]

def after(d):
    """The day after"""
    global daynames
    if not d in daynames:
        return "xxx"
    return daynames[(daynames.index(d)+1)%7]
    

#we'll need these...
daymins = 24*60
daynames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
hournames = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13",
             "14","15","16","17","18","19","20","21","22","23"]

#if you're not called Brian, you'll need to change this line:
me = "brian" #to elminate my own sent mail, which would bias the sample


# get mbox name and read file

Tk().withdraw() # we don't want a full GUI

T = "Email send plotter"

showinfo(title=T,
         message = "I'm going to need an MBOX file.")
fn = (askopenfilename(title="Select MBOX file"))
showinfo(title=T,
         message = "Plots will be saved as PNG in the same folder as the MBOX file.")

raw_mbox = rf(fn)

# separate dates from chaff

raw_dates = []
in_msg = False

for l in raw_mbox:
    if l.startswith("From - "):
        #in a new message
        in_msg = True
        hold_date = None
        ietf = False
        continue
    #get rid of any double spaces
    l = " ".join(l.split())
    if in_msg and l.startswith("Date: "):
        hold_date = l.strip("Date: ").replace(",","").strip("\n")
        continue
    if in_msg and l.startswith("From: ") and me in l.lower():
        #from me, ignore
        hold_date = None
        in_msg = False
        continue
    if in_msg:
        if l.startswith("To: ") or l.startswith("CC: ") or l.startswith("Cc: "):
            if "ietf" in l.lower():
                ietf = True
        
    if in_msg and l.startswith("Subject: "):
        if hold_date and ietf:
            raw_dates.append(hold_date)
        in_msg = False

del raw_mbox
    
print(len(raw_dates), "dated messages with IETF destination")

# split out fields and compute UTC

dates = []

for l in raw_dates:
    day,dd,mo,yr,tm,tz = l.split(" ", maxsplit=5)
    #extract hours & minutes
    thour = duoval(tm[0:2])
    tmin = duoval(tm[3:5])
    #extract time zone offset
    if tz[0] == "+":
        #sender was east of Greenwich (ahead of UTC)
        tzsign = -1
    else:
        #sender was west of Greenwich (behind UTC)
        tzsign = 1
    tzhour = duoval(tz[1:3])
    tzmin = duoval(tz[3:5])
    #recreate UTC
    tmins = 60*thour + tmin
    tzmins = 60*tzhour + tzmin
    umins = tmins + tzsign*tzmins

    if umins > daymins:
        #it's tomorrow already!
        umins = umins - daymins
        uday = after(day)
    elif umins < 0:
        #it's yesterday!
        umins = daymins + umins
        uday = before(day)
    else:
        uday = day
    uhour = umins // 60
    umin = umins % 60
    #print(day, thour, tmin, tzsign, tzhour, tzmin, uday, uhour, umin)
    dates.append(daterec(day, thour, tmin, uday, uhour, umin))

del raw_dates

#now we can compute histograms...

h = []
for i in range(0,24):
    h.append(0)
    
for d in dates:
    h[d.hour] += 1

print("Local hour",h)
fig = plot.figure(figsize = (10, 5))
plot.bar(hournames, h, color ='blue',
        width = 0.4) 
plot.xlabel("Hour")
plot.ylabel("Messages sent")
plot.title("Hourly distribution of messages in sender's local time zone")
plot.savefig(fn+"-hourly-local.png", format="png")
plot.show()



h = []
for i in range(0,24):
    h.append(0)
    
for d in dates:
    h[d.uhour] += 1

print("UTC  hour ",h)
fig = plot.figure(2, figsize = (10, 5))
plot.bar(hournames, h, color ='blue',
        width = 0.4) 
plot.xlabel("Hour")
plot.ylabel("Messages sent")
plot.title("Hourly distribution of messages in UTC")
plot.savefig(fn+"-hourly-UTC.png", format="png")
plot.show()

    
        
wkday=[0,0,0,0,0,0,0]
for d in dates:
    wkday[daynames.index(d.day)] += 1

print("Local day", wkday)
fig = plot.figure(3, figsize = (10, 5))
plot.bar(daynames, wkday, color ='blue',
        width = 0.4) 
plot.xlabel("Day")
plot.ylabel("Messages sent")
plot.title("Daily distribution of messages in sender's local time zone")
plot.savefig(fn+"-daily-local.png", format="png")
plot.show()

wkday=[0,0,0,0,0,0,0]
for d in dates:
    wkday[daynames.index(d.uday)] += 1

print("UTC  day ", wkday)
plot.figure(4, figsize = (10, 5))
plot.bar(daynames, wkday, color ='blue',
        width = 0.4) 
plot.xlabel("Day")
plot.ylabel("Messages sent")
plot.title("Daily distribution of messages in UTC")
plot.savefig(fn+"-daily-UTC.png", format="png")
plot.show()

showinfo(title=T,
         message = "All plots generated!")
    


