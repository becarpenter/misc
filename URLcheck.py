#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Look for broken URLs in RFCs"""

# Version: 2023-05-26
# Version: 2023-05-30 - added DNS retry, gopher/wais count,
#                       certificate mitigations,
#                       better heuristic for non-delimited URLs

########################################################
# Copyright (C) 2023 Brian E. Carpenter.                  
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

# The code attempts to identify all http:, https:, and ftp:
# URLs in all rfcNNNN.txt files in the given directory.
# Isolation of URLs is heuristic due to format variations,
# and URLs split over two lines of text may not be correctly
# handled.

# It then attempts to check each URL for validity.
# However, it only checks a given URL once, and only
# checks a given DNS domain once if it fails, to avoid
# redundant network access. Also, it leaves 5 seconds
# between attempts to limit network traffic.

# Checking links in non-txt versions is left for future work.

# Certificate validity is a tricky area. Two tricks found
# on StackOverflow are in the code. Also, to run on Windows,
# do pip install pip_system_certs

from tkinter import Tk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import askokcancel, askyesno, showinfo

import time
from os import listdir, chdir, getcwd
from os.path import isfile, join
#import os
import urllib.request

import ssl
import certifi

#import binascii

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
    global written
    file = open(f, "w",encoding='utf-8')
    for line in l:
        file.write(line)
    file.close()
    logit("'"+f+"' written")
    written +=1

def check(link, recurse=False):
    """Check a URL and log results."""
    ##Patched out recursive call for https instead of http - didn't solve anything##
    global url, goodies, baddies, baddoms, split_warn, headers, context
    
    request = urllib.request.Request(link, headers=headers)
    try:
        response = urllib.request.urlopen(request, context=context, timeout=30).getcode() 
        if response == 200:
            if recurse:
                goodies.append(url + "(needs https)")
            else:
                goodies.append(url)
        else:
            logit(f+" "+link+split_warn+" "+"HTTP response"+" "+str(response))
            baddies.append(url)
        time.sleep(pause)
    except Exception as E:
        if 'getaddrinfo failed' in str(E):
            if recurse:
                logit(f+" "+link+split_warn+" "+"Socket error"+" "+str(E))
                baddoms.append(dom)
            else:
                #second try at DNS
                time.sleep(DNS_pause)
                check(url, recurse=True)
            
##        elif ( 'certificate verify failed' in str(E) in str(E) )\
##             and 'http://' in url and not recurse:
##            check(url.replace('http://', 'https://'), recurse=True)
        else:
            logit(f+" "+link+split_warn+" "+"Socket error"+" "+str(E))
            baddies.append(url)
        time.sleep(pause)

######### Startup

#Define some globals

printing = False # True for extra diagnostic prints
warnings = 0     # counts warnings in the log file
written = 0      # counts files written
goodies = []     # OK URLs
baddies = []     # Failed URLs
baddoms = []     # Failed domains
gophwais = 0     # count gopher/wais URLs
rfc_count = 0    # RFCs processed

pause = 5        # seconds to wait between attempts
DNS_pause = 20   # seconds to wait after getaddrinfo fail

#Horrible hack to avoid spurious 403 errors on redirected URLs
# - we pretend to be a browser. Thank you StackOverflow!

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'

#Ensure certificates available. Again, thank you StackOverflow!

#print("CA file", certifi.where())
context = ssl.create_default_context(cafile=certifi.where())


#Announce

Tk().withdraw() # we don't want a full GUI

T = "RFC URL checker"

printing = askyesno(title=T,
                    message = "Diagnostic printing?")

where = askdirectory(title = "Select RFC directory")
                   
chdir(where)

#Open log file

flog = open("URLcheck.log", "w",encoding='utf-8')
logit("URLcheck run at "
      +time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime()))

mypath = getcwd()

logit("Running in directory "+ mypath)


showinfo(title=T,
         message = "Will process all RFC txt files")


files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

for f in files:
    if f.startswith("rfc") and f.endswith(".txt"):
        n,_ = f[3:].split(".", maxsplit = 1)
        if not n.isdigit():
            continue
        rfc = rf(f)
        rfc_count += 1
        linex = -1
        while linex < len(rfc)-1:
            #(we do the loop like this to allow look-ahead)
            linex += 1
            line = rfc[linex]            
            #case-normalize the schemes
            line = line.replace("HTTP://","http://").replace("HTTPS://","https://").replace("FTP://","ftp://")
            if not "http://" in line and not "https://" in line and not "ftp://" in line:
                if "wais://" in line.lower():
                    logit(f+" wais URL seen")
                    gophwais += 1
                elif "gopher://" in line.lower():
                    logit(f+" gopher URL seen")
                    gophwais += 1
                continue

            #look for possible terminator
            terminator = None
            if "<http://" in line or "<https://" in line or "<ftp://" in line or "<URL:" in line:
                terminator = ">"
            if "(http://" in line or "(https://" in line or "(ftp://" in line:
                terminator = ")"
            if '"http://' in line or '"https://' in line or '"ftp://' in line:
                terminator = '"'
            if "'http://" in line or "'https://" in line or "'ftp://" in line:
                terminator = "'"
            if "`http://" in line or "`https://" in line or "`ftp://" in line:
                terminator = "'"

            #get rid of prefixed text
            if "http://" in line:
                _,url = line.split("http://", maxsplit = 1)
                url = "http://"+url
            elif "https://" in line:
                _,url = line.split("https://", maxsplit = 1)
                url = "https://"+url
            elif "ftp://" in line:
                _,url = line.split("ftp://", maxsplit = 1)
                url = "ftp://"+url

            #a URL with no delimiter could be splt over two lines
            split_warn = ""
            if not terminator and line.endswith("-\n"):
                #URL reaches end of line
                #No decent heuristic for this case, but we'll add a line anyway
                split_warn = " (split URL?)"
                linex += 1 #safe because there's always junk at the end of an RFC
                url = url.replace("\n","") + rfc[linex].strip()
                 
            #find terminator, including combining split lines
            if terminator:
                if terminator in url:
                    url,_ = url.split(terminator, maxsplit = 1)
                else: #missing a terminator, add next line
                    linex += 1 #safe because there's always junk at the end of an RFC
                    url = url.replace("\n","") + rfc[linex].strip()
                    if terminator in url:
                        url,_ = url.split(terminator, maxsplit = 1)
                    else: #still missing a terminator, add another line
                        linex += 1
                        url = url.replace("\n","") + rfc[linex].strip()
                        if terminator in url:
                            url,_ = url.split(terminator, maxsplit = 1)
                        else:
                            pass #give up on this one, more than 3 lines

            #get rid of spurious stuff          
            url = url.strip().split()[0]

            #get rid of unmatched delimiters
            
            if url.endswith(")."): #both .) and ). have been seen
                url = url[:-2]
            if url.endswith(")"):
                url = url[:-1]
            if url.endswith("."):
                url = url[:-1]
            if url.endswith(">"):
                url = url[:-1]
            if url.endswith(","):
                url = url[:-1]                      
            if url.endswith('"'):
                url = url[:-1]
            if url.endswith("'"):
                url = url[:-1]
                 
            #extract DNS domain
            _,dom = url.split("://", maxsplit=1)
             
            if "/" in dom:
                dom,_ = dom.split("/", maxsplit=1)
            if "example." in dom:
                continue
            if dom in baddoms:
                logit(f+" "+url+" FAILING DOMAIN (see above)")
            elif url in baddies:
                logit(f+" "+url+" FAILING URL (see above)")        
            elif not url in goodies:
                #not already checked, so check it!
                check(url)

                 
                        
                    
######### Finalise log and exit

logit("\n"+str(rfc_count)+" RFCs processed")
logit(str(len(goodies))+" good URLs found")
logit(str(len(baddoms))+" non-existent domains found")
logit(str(len(baddies))+" failing URLs found")
logit(str(gophwais)+" gopher or wais URLs found")
logit("URLcheck ended at "
      +time.strftime("%Y-%m-%d %H:%M:%S UTC%z",time.localtime()))
    
flog.close()

if warnings:
    warn = str(warnings)+" warning(s)\n"
else:
    warn = ""

if written:
    wrote = str(written)+" file(s) written.\n"
else:
    wrote = "Clean run.\n"

showinfo(title=T,
         message = wrote+warn+"Check URLcheck.log.")
