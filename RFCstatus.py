#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find obsoleted normative RFCs"""

# Version: 2024-12-18 - original
# Version: 2024-12-19 - tag obsoleted STDs with unknown STD number
#                     - list IS separately from DS & PS


########################################################
# Copyright (C) 2023-24 Brian E. Carpenter.                  
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
import os
import sys
import requests

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
    if fname in block:
        _,temp = block.split("<"+fname+">", maxsplit=1)
        result,_ = temp.split("</"+fname+">", maxsplit=1)
        return result
    return ""
    

def title(block):
    """Extract title from XML block"""
    return field("title", block)

def doc_id(block):
    """Extract doc-id from XML block"""
    return field("doc-id", block)  

def interesting(block):
    """Save interesting RFC data from XML block"""
    global stds, bcps
    if "UNKNOWN" in block:
        return False
    elif "<current-status>HISTORIC" in block:
        return False
    elif not "<obsoleted-by>" in block:
        return False
    else:
        #Potentially interesting
        #print(block)
        status = field("current-status", block)
        if "is-also" in block:
            also,_ = field("is-also", block).split("<doc-id>")[1].split("</")
            if also.startswith("BCP0"):
                also = " (BCP"+also[3:].lstrip("0")+")"
            elif also.startswith("STD0"):
                also = " (STD"+also[3:].lstrip("0")+")"
        elif status == "INTERNET STANDARD":
            also = " (STD?)"
        else:
            also = ""
        #print("Also: ",also)
        if status == "INTERNET STANDARD":
            istds.append(doc_id(block)+also+": "+title(block))
        elif "STANDARD" in status:
            stds.append(doc_id(block)+also+": "+title(block))
        elif status == "BEST CURRENT PRACTICE":
            bcps.append(doc_id(block)+also+": "+title(block))
        return True
    return False

######### Startup

#Define some globals

inrfc = False
new = ''
numberfound = False
count = 0
stds = []
istds = []
bcps = []
printing = False # True for extra diagnostic prints
warnings = 0

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

    T = "Obsoleted Normative RFCs lister."

    printing = askyesno(title=T,
                        message = "Diagnostic printing?")

    os.chdir(askdirectory(title = "Select directory"))
                   


#Open log file

flog = open("RFCstatus.log", "w",encoding='utf-8')
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())
logit("RFCstatus run at "+timestamp)

logit("Running in directory "+ os.getcwd())


show("Will read complete RFC index.")

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
whole = rf(fp)
  
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())

for line in whole:
    #print(line)
    if (not inrfc) and (not "<rfc-entry>" in line):
        continue
    inrfc = True
    new += line
    if inrfc and "</rfc-entry>" in line:
        #end of an rfc entry
        if interesting(new):         
            count += 1
        inrfc = False
        numberfound = False
        new = ''
        continue
    
logit(str(count)+" obsoleted non-historic RFCs found")

md = ["## RFC status","",
      "This is a list of all obsoleted normative RFCs that are not marked Historic"]
md += ["","RFC status run at "+timestamp]
md += ["","### Internet Standards ("+str(len(istds))+" RFCs)",""]
md += istds
md += ["","### Draft or Proposed Standards ("+str(len(stds))+" RFCs)",""]
md += stds
md += ["", "### Best Current Practice ("+str(len(bcps))+" RFCs)", ""]
md += bcps

wf("RFCstatus.md", md)

######### Close log and exit
    
flog.close()

if warnings:
    warn = str(warnings)+" warning(s)\n"
else:
    warn = ""

show(warn+"Check RFCstatus.log.")
    

    
