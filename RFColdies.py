#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Analyse legacy/unknown/historic/obsoleted RFCs"""

# Version: 2025-01-01 - original


########################################################
# Copyright (C) 2023-25 Brian E. Carpenter.                  
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
import xmltodict

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
    return block["title"]

def doc_id(block):
    """Extract doc-id from XML block"""
    return block["doc-id"] 

def interesting(block):
    """Extract interesting RFC data from XML block"""
    global rfcs, std_count, fyi_count, bcp_count
    status = block['current-status']
    unknown = status == "UNKNOWN"
    historic = status == "HISTORIC"
    legacy = block["stream"] == "Legacy"    
    if field("obsoleted-by", block):
        obsolete = True
    else:
        obsolete =False
    if unknown or historic or legacy or obsolete:
        #Potentially interesting
        #print(block)
        if field("is-also", block):
            also = block["is-also"]["doc-id"]
            if also.startswith("BCP0"):
                also = " (BCP"+also[3:].lstrip("0")+")"
                bcp_count += 1
            elif also.startswith("STD0"):
                also = " (STD"+also[3:].lstrip("0")+")"
                std_count += 1
            elif also.startswith("FYI0"):
                also = " (FYI"+also[3:].lstrip("0")+")"
                fyi_count += 1
        elif status == "INTERNET STANDARD":
            also = " (STD?)"
            std_count += 1
        elif status == "PROPOSED STANDARD":
            also = " (PS)"
        elif status == "DRAFT STANDARD":
            also = " (DS)"
        elif status == "INFORMATIONAL":
            also = " (Info)"
        elif status == "EXPERIMENTAL":
            also = " (Exp)"
            
        else:
            also = ""
        #print("Also: ",also)
        new = {}
        new["doc-id"] = (block["doc-id"])
        new["legacy"] = legacy
        new["unknown"] = unknown
        new["historic"] = historic
        new["obsolete"] = obsolete
        new["also"] = also        
        rfcs.append(new)
        return True
    return False

######### Startup

#Define some globals

inrfc = False

count = 0
std_count = 0
bcp_count = 0
fyi_count = 0
rfcs = []
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

flog = open("RFColdies.log", "w",encoding='utf-8')
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())
logit("RFColdies run at "+timestamp)

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
xf = open(fp,"r",encoding='utf-8', errors='replace')
index_dict = xmltodict.parse(xf.read())
xf.close()
all_rfcs = index_dict['rfc-index']['rfc-entry']
  

for r in all_rfcs:
    if interesting(r):         
        count += 1

    
logit(str(count)+" oldish RFCs found")

md = ["## RFC oldies","",
      "This is a list of all oldish RFCs. The criterion is that the"]
md += ["RFC Index shows them as Legacy, UNKNOWN, HISTORIC or obsoleted.\n"]
md += ["","RFColdies run at "+timestamp, ""]

md += [str(count)+" oldish RFCs found, including:"]
md += [str(std_count)+" Internet Standards, "+str(bcp_count)+" BCPs and "+str(fyi_count)+" FYIs.\n"]

count2 = 0
count3 = 0

for rfc in rfcs:
    counts = 0
    counts += 1 if rfc["legacy"] else 0
    counts += 1 if rfc["unknown"] else 0
    counts += 1 if rfc["historic"] else 0
    counts += 1 if rfc["obsolete"] else 0
    count2 += 1 if counts == 2 else 0
    count3 += 1 if counts == 3 else 0

md += [str(count2)+" RFCs meet 2 criteria."]
md += [str(count3)+" RFCs meet 3 criteria.\n"]

    

for rfc in rfcs:
    new = rfc["doc-id"]+" "
    new += "Legacy " if rfc["legacy"] else "       "
    new += "UNKNOWN " if rfc["unknown"] else "        "
    new += "HISTORIC " if rfc["historic"] else "         "
    new += "Obsolete " if rfc["obsolete"] else "         "
    new += rfc["also"]
    md += [new]
 
    

wf("RFColdies.md", md)

######### Close log and exit
    
flog.close()

if warnings:
    warn = str(warnings)+" warning(s)\n"
else:
    warn = ""

show(warn+"Check RFColdies.log.")
    

    
