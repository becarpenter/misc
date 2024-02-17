#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Analyse obsoleted/obsoleting RFCs"""

# Version: 2024-02-17 - original


########################################################
# Copyright (C) 2024 Brian E. Carpenter.                  
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
import requests

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

def tot_up(item):
    global nochange
    head, tail = item.split(" obsoleted ")
    _, head = head.split(" ", maxsplit=1)
    tail, _ = tail.rsplit(" ", maxsplit=1)
    #print(head,tail,head==tail)
    if head == tail:
        nochange += 1
    else:
        orig = states.index(tail)
        new = states.index(head)
        counts[orig][new] += 1
                          

def field(fname, block):
    """Extract 1st version of a named field from XML block"""
    if fname in block:
        _,temp = block.split("<"+fname+">", maxsplit=1)
        result,_ = temp.split("</"+fname+">", maxsplit=1)
        return result
    return ""
    

def title(block):
    """Extract 1st title from XML block"""
    return field("title", block)

def doc_id(block):
    """Extract 1st doc-id from XML block"""
    return field("doc-id", block)  

def obsoleted(block):
    """Save obsolescence data from XML block"""
    global stds
    if "<obsoleted-by>" in block:
        #print(block)
        statuses.append(field("current-status", block)+" "+doc_id(block))
        i=block.index("<obsoleted-by>")
        obsols.append(field("doc-id", block[i:]))
        return True
    else:        
        return False


def obsoleting(block):
    """Complete obsolescence data from XML block"""
    global obsols, statuses, results
    if doc_id(block) in obsols:
        status = field("current-status", block)
        old = statuses[obsols.index(doc_id(block))]     
        result = doc_id(block)+" "+status+" obsoleted "+old
        tot_up(result)
        results.append(result)
        return True
    else:        
        return False
    

######### Startup

#Define some globals

inrfc = False
new = ''
numberfound = False
count = 0
nochange = 0
obsols = []
statuses = []
results = []
states = ["UNKNOWN","HISTORIC","PROPOSED STANDARD","DRAFT STANDARD",
          "INTERNET STANDARD", "BEST CURRENT PRACTICE", "EXPERIMENTAL",
          "INFORMATIONAL"]
abbrevs = ["UNK","HIS","PS ","DS ","IS ","BCP","EXP","INF"]
header = "    "
for x in abbrevs:
    header += x+" "
counts = [[0 for col in range(len(states))] for row in range(len(states))]
printing = False # True for extra diagnostic prints
warnings = 0

#Announce

Tk().withdraw() # we don't want a full GUI

T = "Analyse RFC obsolescence"

printing = askyesno(title=T,
                    message = "Diagnostic printing?")



#Open log file

flog = open("obsol.log", "w",encoding='utf-8')
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())
logit("obsol run at "+timestamp)

logit("Running in directory "+ os.getcwd())


showinfo(title=T,
         message = "Will read complete RFC index.\nTouch no files until done!")

fp = "rfc-index.xml"
if (not os.path.exists(fp)) or (time.time()-os.path.getmtime(fp) > 60*60*24*30):
    #need fresh copy of index
    try:
        if askyesno(title=T, message = "OK to download RFC index?\n(15 MB file)"):
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
    if (not inrfc) and (not "<rfc-entry>" in line):
        continue
    inrfc = True
    new += line
    if inrfc and "</rfc-entry>" in line:
        #end of an rfc entry
        if obsoleted(new):         
            count += 1
        inrfc = False
        numberfound = False
        new = ''
        continue  

for line in whole:
    if (not inrfc) and (not "<rfc-entry>" in line):
        continue
    inrfc = True
    new += line
    if inrfc and "</rfc-entry>" in line:
        #end of an rfc entry
        if obsoleting(new):         
            count += 1
        inrfc = False
        numberfound = False
        new = ''
        continue
    
logit(str(len(obsols))+" obsoleted RFCs found")
logit(str(nochange)+": no change of status\n")
logit(header+"  <-- new status")
for i in range(len(states)):
    out = abbrevs[i]
    for j in range(len(states)):
        out += " " +format(counts[i][j], '03d')
    logit(out)
logit("|\n|___old status\n")

wf("obsoleters.txt", results)

######### Close log and exit
    
flog.close()

if warnings:
    warn = str(warnings)+" warning(s)\n"
else:
    warn = ""

showinfo(title=T,
         message = warn+"Done, summary in obsol.log")
    

    
