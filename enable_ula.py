#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""########################################################
########################################################
#                                                     
# ULA enabler (enable_ula.py)     
#                                                                                                        
# This program enables effective ULA use by updating
# the RFC6724 policy table to give any locally active
# ULA prefixes precedence over IPv4 (and in particular
# over RFC1918 addresses).
#
# It's intended to work on Windows or POSIX-compliant
# systems. It needs to be run once after every
# system restart (boot). It does no harm to run this
# program more than once.
#
# On Windows, the only changes made are to the "active"
# policy table, which will be lost at next boot.
# Open a command prompt running as Administrator, and
# type "python enable_ula.py" without the quotes.
#
# On Linux, the /etc/gai.conf file is overwritten. Also,
# changes are made to the active label table, which will
# be lost at next boot. At a shell prompt, type
# "sudo python3 enable_ula.py" without the quotes.
#
# Other POSIX-compliant operating systems are for future
# work.
#
########################################################
#
# Released under the BSD "Revised" License as follows:
#                                                     
# Copyright (C) 2022 Brian E. Carpenter.                  
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
########################################################"""

import os
import ctypes
import sys
import socket
import ipaddress
import subprocess

def askexit():
    """Get me outa here"""
    input("Press Enter to Exit.")
    exit()

def is_ula(a):
    """Test for ULA"""
    return (a.is_private and not a.is_link_local
             and not a.is_loopback
             and not a.is_unspecified)

def wincmd(cmd):
    """Execute Windows command and display results"""
    #(Separate function in case of o/s dependencies)
    #print("Debug: ",cmd)
    do_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _out, _err = do_cmd.communicate()
    if _err:
        print(_err.decode('utf-8').strip())
    if _out:
        _out = _out.decode('utf-8').strip()
        print(_out)
        if "requires elevation" in _out:
            askexit()

def shcmd(cmd):
    """Execute shell command and display results"""
    #(Separate function in case of o/s dependencies)
    #print("Debug: ",cmd)
    do_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _out, _err = do_cmd.communicate()
    if _err:
        print(_err.decode('utf-8').strip())
    if _out:
        print(_out.decode('utf-8').strip())

# Default RFC6724 policy table in Linux gai.conf format
deftab = [
    "label ::1/128 0",
    "label ::/0 1",
    "label ::ffff:0:0/96 4",
    "label 2002::/16 2",
    "label 2001::/32 5",
    "label fc00::/7 13",
    "label ::/96 3",
    "label fec0::/10 11",
    "label 3ffe::/16 12",
    "precedence ::1/128 50",
    "precedence ::/0 40",
    "precedence ::ffff:0:0/96 35",
    "precedence 2002::/16 30",
    "precedence 2001::/32 5",
    "precedence fc00::/7 3",
    "precedence ::/96 1",
    "precedence fec0::/10 1",
    "precedence 3ffe::/16 1"
    ]


print("=====================================================")
print("This program attempts to set IPv6 policy so that ULAs")
print("(Unique Local Addresses) will be used for internal")
print("sessions, if they are defined.")
print("=====================================================")

print("This is experimental software that might disturb network access.")
_l = input("Continue? Y/N: ")
if _l:
    if _l[0] != "Y" and _l[0] != "y":
        exit()
else:
    exit()

my_os = sys.platform

if my_os == "win32":
    print("You are running on Windows.")
else:
    print("Assuming a POSIX-compliant operating system.")
    try:
        import netifaces
    except:
        print("Could not import netifaces - please install with pip or apt-get.")
        askexit()
    



####################################################
# Get list of ULAs
#
# This code is very o/s dependent
####################################################

ulas = []
if my_os == "win32":
    #Windows
          
    _addrinfo = socket.getaddrinfo(socket.gethostname(),0)
    for _af,_temp1,_temp2,_temp3,_addr in _addrinfo:
        if _af == socket.AF_INET6:
            _addr,_temp,_temp,_zid = _addr  #get first item from tuple
            
            if not '%' in _addr:
                _loc = ipaddress.IPv6Address(_addr)
                # Now test for  ULA address
                if is_ula(_loc):
                    ulas.append(_loc)  # save ULA
        
else: #assume POSIX     
    ifs = netifaces.interfaces()
    for interface in ifs:
        config = netifaces.ifaddresses(interface)
        if netifaces.AF_INET6 in config.keys():
            for link in config[netifaces.AF_INET6]:
                if 'addr' in link.keys():
                    _addr = link['addr']
                    if not '%' in _addr:
                        _loc = ipaddress.IPv6Address(_addr)
                        # Now test for ULA
                        if is_ula(_loc):
                            ulas.append(_loc)  # save ULA

if not len(ulas):
    print("No active ULA found.")
    askexit()


# Convert addresses to prefixes as text strings
prefs = []
print("ULA prefix(es) found:")
for a in ulas:
    #strip to /48
    a = ipaddress.IPv6Address(a.packed[:6]+bytes.fromhex('00000000000000000000'))
    p = str(a) + "/48"
    if not p in prefs:
        prefs.append(p)
for p in prefs:
    print(p)

# Build commands to add precedence and issue them

print("Will now update prefix policy table.")

if my_os == "win32":
    #Windows

    #It seems safe to assume Windows starts with a correct RFC6724 default table

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Cannot run without Administrator privilege.")
        askexit()
    
    for p in prefs:
        cmd = "netsh interface ipv6 add prefixpolicy " + p + " 45 14 active"
        #(This MUST be 'active' because doing otherwise triggers a serious
        # Windows bug that clears the rest of the policy table on the
        # next boot.)
        wincmd(cmd)

    print("Current prefix policies:")
    wincmd("netsh interface ipv6 show prefixpolicies")

elif my_os == "linux" or my_os == "linux2":
    #Linux

    #It seems necessary to assume that Linux starts with a broken configuration
    #based on obsolete RFC3484.

    print("Original prefix labels (precedence not shown):")
    shcmd("ip addrlabel show")

    #Apart from that, for some understanding of what happens next,
    #see Karl Auer's blog from 2012 at http://biplane.com.au/blog/?p=122
    
    #Create default /etc/gai.conf configuration

    print("The program will overwrite /etc/gai.conf with RFC6724 default settings.")
    _l = input("Continue? Y/N: ")
    if _l:
        if _l[0] != "Y" and _l[0] != "y":
            exit()
    else:
        exit()    
    try:
        gaifile = open("/etc/gai.conf", "w")
    except:
        print("Cannot open /etc/gai.conf for write; need root (sudo) privilege")
        askexit()
    print("Will add RFC6724 default policy in /etc/gai.conf.")
    gaifile.write("\n# Defaults set exactly according to RFC6724.")
    shcmd("ip addrlabel flush")  #if we crash now, the active label table is 100% empty
    for line in deftab:
        gaifile.write("\n"+line)
        if line[:5] == "label":
            #add this label to the active label table
            _,_pfx,_lbl = line.split(" ")
            cmd = "ip addrlabel add prefix " + _pfx + " label " + _lbl
            shcmd(cmd)
    print("Will add local ULA configuration.")
    gaifile.write("\n# Local ULA preferred over IPv4.")
    for p in prefs:
        #add two lines to gai.conf      
        gaifile.write("\nlabel " + p + " 14")
        gaifile.write("\nprecedence " + p + " 45")
        #add prefix label to active table
        shcmd("ip addrlabel add prefix " + p + " label 14")
    gaifile.close()
    print("Final prefix labels (precedence not shown):")
    shcmd("ip addrlabel show")
else:
    print("Platform", my_os, "not yet supported.")
    askexit()

print("All done.")
askexit()





    


    
