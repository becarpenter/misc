#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Email name collector. It builds sender name sets for 
emails sent to IETF destinations, based on an email
file in MBOX format.
No warranty. Use, copy and modify as you wish, at your own risk.""" 

from tkinter import Tk
from tkinter.filedialog import askopenfilenames
from tkinter.messagebox import showinfo
from tkinter.simpledialog import askstring
from email.header import decode_header

def rf(f):
    """Return a file as a list of strings"""
    file = open(f, "r",encoding='utf-8', errors='replace')
    l = file.readlines()
    file.close()
    return l

# get mbox name and read file

Tk().withdraw() # we don't want a full GUI

T = "Email name collector"

showinfo(title=T,
         message = "I'm going to need one or more MBOX files.")
fns = (askopenfilenames(title="Select MBOX file(s)"))
showinfo(title=T,
         message = "File will be saved in the same folder as the first MBOX file.")

tag = askstring(T, "Enter meaningful identifier for output file")
if len(tag) < 1:
    tag = "mbox"

tagstring = " ("+tag+")"

me = askstring(T, "Enter string to exclude matching senders (or nil)")
if len(me) > 3:
    showinfo(title=T,
         message = "Senders that include '"+me+"' will be excluded")
else:
    me = ""


fn,_ = fns[0].rsplit("/",1)
fn = fn  + "/" + tag

raw_mbox = []
for f in fns:
    raw_mbox.extend(rf(f))

# separate names from chaff

raw_names = []
in_msg = False

for l in raw_mbox:
    if l.startswith("From - ") or l.startswith("From nobody "):
        #in a new message
        in_msg = True
        ietf = False
        continue
    
    #get rid of any double spaces
    l = " ".join(l.split())

    if in_msg and l.startswith("From: "):
        if me and me in l.lower():
            #from me, ignore
            in_msg = False
        else:
            #extract sender name if present
            name = None
            #remove any double quotes
            if l[6:].startswith('"'):
                l = l.replace('"','')
            #decode UTF-8
            if l[6:].lower().startswith('=?utf-8'):
                #encoded
                coded, tail = l[6:].rsplit("?=", 1)
                decoded = decode_header(coded+"?=")[0][0].decode('utf-8')
                l = l[0:6] + decoded + tail
            #attempt extraction
            try:
                if l.startswith("From: <"):
                    #no display name but email inside <...>, get username
                    name,_ = l[7:].split("@",1)
                    
                elif "<" in l:
                    #extract display name
                    
                        name,_ = l[6:].split(" <",1)
                        name = name.replace(" via Datatracker", "")                
                    
                elif "@" in l:
                    #plain email, get username
                    name,_ = l[6:].split("@",1)
                else:
                    #display name alone???
                    name = l[6:].replace(" via Datatracker", "")
            except:
                #unhandled format, ignore
                print("UNHANDLED: ", l)
                
            if name and (not name in raw_names):
                raw_names.append(name)
        continue
    
    if in_msg:
        #if l.startswith("To: ") or l.startswith("CC: ") or l.startswith("Cc: "):
        #(That doesn't work because these lines can split, so we'll be lazy)
        if "ietf.org" in l.lower():
            ietf = True
            
    if in_msg and len(l)<1: #blank line terminates headers
        in_msg = False

del raw_mbox
    
print(len(raw_names), "sender names with IETF destination")
#print(raw_names)

# write file

o = open(fn+"-names.txt","w",encoding='utf-8', errors='replace')
for l in raw_names:
    try:
        o.write(l+"\n")
    except:
        print("INVALID",l)
        o.write(l[0:5]+" !invalid character\n" )
o.close()


showinfo(title=T,
         message = "List saved")
    


