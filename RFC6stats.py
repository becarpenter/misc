#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collect IPv6 RFC statistics"""

# Version: 2026-05-18 - fork off from RFCbib6 to focus on statistics.
#                       This version is rough and ready.

########################################################
# Copyright (C) 2023-26 Brian E. Carpenter.                  
# All rights reserved.
#
# Redistribution and use in source and binary forms, with
# or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above
# copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials
# provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of
# its contributors may be used to endorse or promote products
# derived from this software without specific prior written
# permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS  
# AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED 
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A     
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)    
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING   
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE        
# POSSIBILITY OF SUCH DAMAGE.                         
#                                                     
########################################################

from tkinter import Tk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import askokcancel, askyesno, showinfo

import time
import datetime
import os
import sys
import requests
import xmltodict
from copy import deepcopy

def show(msg):
    """Show a message"""
    global T, cmd_line
    if cmd_line:
        print(msg)
    else:
        showinfo(title=T, message = msg)

def logit(msg):
    """Add a message to the log file"""
    global flog, printing
    flog.write(msg+"\n")
    if printing:
        print(msg)
        
def logitw(msg):
    """Add a warning message to the log file"""
    global warnings
    logit("WARNING: "+msg)
    warnings += 1

def dprint(*msg):
    """ Diagnostic print """
    global printing
    if printing:
        print(*msg)

def crash(msg):
    """Log and crash"""
    global printing
    printing = True
    logit("CRASH "+msg)
    flog.close()
    exit() 

def rf(f):
    """Return a file as a list of strings"""
    file = open(f, "r",encoding='utf-8', errors='replace')
    l = file.readlines()
    file.close()
    #ensure last line has a newline
    if l[-1][-1] != "\n":
        l[-1] += "\n"
    return l

def wf(f,l):
    """Write list of strings to file"""
    file = open(f, "w",encoding='utf-8')
    for line in l:
        file.write(line+"\n")
    file.close()
    logit("'"+f+"' written")

def field(fname, block):
    """Extract named field from XML block"""
    try:
        return block[fname]
    except:
        return None      

def title(block):
    """Extract title from XML block"""
    return field("title", block)

def doc_id(block):
    """Extract doc-id from XML block"""
    return field("doc-id", block)  

def interesting(block):
    """Save interesting RFC data from XML block"""
    global stds, bcps, infos, exps, statlist
    
##    if status in ["UNKNOWN", "HISTORIC"]:
##        return False
##    elif field("obsoleted-by", block):
##        return False
    if ("IPv6" in block['title'] or "IP Version 6" in block['title'] or "DHCPv6" in block['title']
          or "NAT64" in block['title'] or "DNS64" in block['title'] or "464XLAT" in block['title']
          or (field("wg_acronym", block) in wgs)):
        #print(block)
        new = stat(doc_id(block))
        new.year = block["date"]["year"]
        status = block["current-status"]
        new.coexist = ("NAT64" in block['title'] or "DNS64" in block['title'] or "464XLAT" in block['title']
            or "IPv4" in block['title'])
        new.obsoleted = bool(field("obsoleted-by", block))
        new.obsoleting = bool(field("obsoletes", block))
        new.standard = "STANDARD" in status
        new.BCP = status == "BEST CURRENT PRACTICE"
        new.info = status =="INFORMATIONAL"
        new.expt = status == "EXPERIMENTAL"
        new.ietf = block["stream"] == "IETF"
        if field("is-also", block):
            also = block["is-also"]["doc-id"]
            new.BCP = also.startswith("BCP")
            new.STD = also.startswith("STD")
        statlist.append(new)
        return True
    return False

######### Startup

class stat:
    """Statistics for one RFC"""
    def __init__(self, docid):
        self.docid = docid  #the RFC's name
        self.year = 0
        self.coexist = False
        self.obsoleted = False
        self.obsoleting = False
        self.standard = False
        self.BCP = False
        self.STD = False
        self.expt = False
        self.info = False
        self.ietf = False

#Define some globals

inrfc = False
new = ''
numberfound = False
count = 0
stds = []
bcps = []
infos= []
exps = []
printing = False # True for extra diagnostic prints
warnings = 0
wgs = ["6man","v6ops"]

statlist = []

#Has the user supplied a directory on the command line?

cmd_line = False
if len(sys.argv) > 1:
    #user provided directory name?
    if os.path.isdir(sys.argv[1]):
        #assume user has provided directory
        #and set all options to defaults
        os.chdir(sys.argv[1])
        cmd_line = True

#Announce
if not cmd_line:
    Tk().withdraw() # we don't want a full GUI

    T = "IPv6 RFC statistics gatherer."

    printing = askyesno(title=T,
                        message = "Diagnostic printing?")

    os.chdir(askdirectory(title = "Select main book directory"))
                   


#Open log file

flog = open("RFC6stats.log", "w",encoding='utf-8')
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())
logit("RFC6stats run at "+timestamp)

logit("Running in directory "+ os.getcwd())


show("Will read complete RFC index.\nTouch no files until done!")

fp = "rfc-index.xml"
if (not os.path.exists(fp)) or (time.time()-os.path.getmtime(fp) > 60*60*24*30):
    #need fresh copy of index
    try:
        if cmd_line or askyesno(title=T, message = "OK to download RFC index?\n(15 MB file)"):
            response = requests.get("https://www.rfc-editor.org/rfc/rfc-index.xml")
            open(fp, "wb").write(response.content)
            logit("Downloaded and cached RFC index")
        else:
            raise Exception("Invalid choice")
    except Exception as E:
        logitw(str(E))
        crash("Cannot run without RFC index")
xf = open(fp,"r",encoding='utf-8', errors='replace')
index_dict = xmltodict.parse(xf.read())
xf.close()
all_rfcs = index_dict['rfc-index']['rfc-entry']
  
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())

for r in all_rfcs:
    if interesting(r):         
        count += 1
    
logit(str(count)+" IPv6 RFCs found")

## process statistics (rough and ready)

obsolete = 0
year_counts = []
for i in range(1995,int(datetime.date.today().year)+1):
    year_counts.append(0)
year_coex = deepcopy(year_counts)
non_ietf = 0
std_track = 0
bcps =0
infos = 0
exps = 0
coexists = 0
               

for x in statlist:
    year_counts[int(x.year)-1995] += 1      
    if x.obsoleted:
        obsolete +=1
    if not x.ietf:
        non_ietf +=1
    if x.standard:
        std_track +=1
    if x.BCP:
        bcps +=1
    if x.info:
        infos +=1
    if x.expt:
        exps +=1
    if x.coexist:
        year_coex[int(x.year)-1995] += 1
        coexists +=1
print("Obsoleted:", obsolete)
print("Not IETF stream:", non_ietf)
print("Related to v4/v6 coexistence:", coexists)
print("Standards track and BCPs:", std_track + bcps)
print("Informational", infos)
print("Experimental", exps)
      
print("Yearly RFCs & Coexistence RFCs:")

for i in range(len(year_counts)):
    print(i+1995, year_counts[i], year_coex[i])

######### Close log and exit
    
flog.close()

if warnings:
    warn = str(warnings)+" warning(s)\n"
else:
    warn = ""

show(warn+"Check RFC6stats.log.")
    

    
