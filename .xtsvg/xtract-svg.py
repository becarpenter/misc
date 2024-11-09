#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract SVG figures from HTML file of an RFC"""

# Brian Carpenter 24/11/2023
# Rough and ready code, use at your own risk
# License: DWTFYWWI

from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showinfo
import os

def rf(f):
    """Return a file as a list of strings"""
    file = open(f, "r",encoding='utf-8', errors='replace')
    l = file.readlines()
    file.close()
    return l

def wf(f,l):
    """Write list of strings to file"""
    global count
    file = open(f, "w",encoding='utf-8')
    for line in l:
        file.write(line)
    file.close()
    count +=1 

def ask_exit(m):
    """Get out of here"""
    showinfo(title=T, message = m)
    exit(0)

#Initialise

count = 0

#Announce

Tk().withdraw() # we don't want a full GUI

T = "SVG extractor for an HTML RFC."

showinfo(title=T,
         message = "I'm going to need an input HTML file.")

#Get input file

fn = (askopenfilename(title="Select input HTML file"))

#Get local directory and filename

ldir, _, lfn= fn.rpartition('/')

lfn, _, ftype = lfn.rpartition('.')
if not ftype.lower() in ('html','htm','xhtml'):
    showinfo(title=T,
         message = "Warning: unexpected file type.")

#Make directory name for output files

if not lfn:
    lfn = ftype     #special case of blank file type
ldir = ldir+"/"+lfn+"-figs"

if not os.path.isdir(ldir):
    os.mkdir(ldir)

#Read input

raw = rf(fn)
if not len(raw):
    ask_exit("Empty input")

#Delete blank lines for simplicity
text = []
for line in raw:
    if line.strip():
        text.append(line)
del raw

#Sanity check
if not text[0].startswith("<!DOCTYPE html>"):
    ask_exit("Invalid input")

in_fig = False
in_svg = False
in_caption = False

for line in text:
    if "<figure" in line:
        in_fig = True
        svg = []
        caption = ''
        continue
    if in_fig and "<svg" in line:
        #Start saving
        in_svg = True
        svg.append(line)
        continue
    if in_fig and in_svg:
        if "</svg>" in line:
            #End of svg - but still need caption
            svg.append("</svg>\n")
            in_svg = False
        else:
            svg.append(line)
        continue
    if in_fig and not in_svg:
        if "<figcaption>" in line:
            in_caption = True
            continue
    if in_fig and in_caption:
        if "<a href=" in line:
            #extract caption
            in_caption = False
            _,tail = line.split(">",1)
            caption,_ = tail.split("<",1)
            caption = caption.replace(" ","_")
        continue
    if in_fig and "</figure>" in line:
        in_fig = False
        #write the SVG file
        wf(ldir+"/"+caption+".svg", svg)    

showinfo(title=T,
         message = str(count)+" SVG file(s) written.")
