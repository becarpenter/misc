#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find trivial errata"""

# Version: 2024-12-20 - original
# Version: 2024-12-21 - some tidying & caching
# Version: 2024-12-21 - cosmetics
# Version: 2024-12-24 - switch to proper xml parser (for speed)

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
import json
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

def getblock(docid):
    """Get dictionary for a given RFC"""
    #if it's in the cache, we're done
    try:
        return(b_cache[docid])
    except:
        pass
    #not in cache, search the whole list
    new = [r for r in all_rfcs if r['doc-id'] == docid]
    if len(new) == 1:
        b_cache[docid] = new[0]
        return new[0]
    else:
        return False



######### Startup

#Define some globals


printing = False # True for extra diagnostic prints
warnings = 0
b_cache = {}

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

    T = "Find trivial errata."

    printing = askyesno(title=T,
                        message = "Diagnostic printing?")

    os.chdir(askdirectory(title = "Select directory"))
                   


#Open log file

flog = open("triviata.log", "w",encoding='utf-8')
timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime())
logit("triviata run at "+timestamp)

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

show("Will read errata.json")

fp = "errata.json"
if (not os.path.exists(fp)) or (time.time()-os.path.getmtime(fp) > 60*60*24*30):
    #need fresh copy of errata
    try:
        if cmd_line or askyesno(title=T, message = "OK to download errata.json?\n(10 MB file)"):
            response = requests.get("https://www.rfc-editor.org/errata.json")
            open(fp, "wb").write(response.content)
            logit("Downloaded and cached errata.json")
        else:
            raise Exception("Invalid choice")
    except Exception as E:
        logitw(str(E))
        crash("Cannot run without errata.json")

jf=open(fp)
errata=json.load(jf)
jf.close()

ct = 0
ect = 0
old_ct = 0
dead_ct = 0
trivia = []
for e in errata:
    if e['errata_status_code'] == 'Reported':
        ct += 1
        year = e['submit_date'][0:4]
        editorial = e['errata_type_code'] == 'Editorial'
        docid = e['doc-id']
        err_id = e['errata_id']
        #print(err_id)
        if editorial:
            ect += 1
        #find info for the RFC
        b = getblock(docid)
        # if unknown, obsoleted, historic, or legacy - erratum is trivial
        if b['current-status']=='UNKNOWN' or b['current-status']=='HISTORIC' or field('obsoleted-by',b) or b['stream']=='Legacy':
            trivia += ["Erratum "+err_id+" on "+docid+" (dead RFC)"]
            dead_ct += 1
        # if editorial before 2020 - erratum trivial
        elif editorial and int(b['date']['year']) < 2020:
            trivia += ["Erratum "+err_id+" on "+docid+" (old editorial)"]
            old_ct += 1
           
logit(str(ct)+" open errata checked, "+str(ect)+" were editorial")

md = ["## Trivial errata","",
      "This is a list of "+str(len(trivia))+" errata reports suggested for rejection",""]
md += ["Generated at "+timestamp,""]
md += [str(ct)+" open reports were checked, of which "+str(ect)+" were editorial."]

md += [str(dead_ct)+" rejects concern dead RFCs (UNKNOWN, HISTORIC, LEGACY or Obsoleted)."]
md += [str(old_ct)+" rejects are editorial reports on pre-2020 RFCs.",""]
md += trivia

wf("triviata.md", md)

######### Close log and exit
    
flog.close()

if warnings:
    warn = str(warnings)+" warning(s)\n"
else:
    warn = ""

show(warn+"Check triviata.log.")
    

    
