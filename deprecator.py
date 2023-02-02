#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""########################################################
########################################################
#                                                     
# Source address deprecator (deprecator.py)     
#                                                                                                        
# This program attempts to deprecate IPv6 globally
# routable source addresses when they are shown by
# probing to be broken, and to undeprecate them when
# they seem to work again. This could run in background
# on any host.
#
# It's intended to work on Windows or POSIX-compliant
# systems. It needs to be started after every
# system restart (boot). It needs root/Administrator
# privilege.
#
# On Windows, we use
# 'netsh int ipv6 set address $ADDR preferredlifetime=0 store=active'
# to deprecate the broken address.
#
# On Linux, we use
# 'ip addr change $ADDR/64 dev $INTERFACE preferred_lft 0'
# to deprecate the broken address.
#
# Other POSIX-compliant operating systems: TBD.
#
########################################################
#
# Released under the BSD "Revised" License as follows:
#                                                     
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
########################################################"""

#Version 2 - uses RIPE Atlas anchor probes as target

import os
import ctypes
import sys
import socket
import ipaddress
import subprocess
import time
import random # used for testing
try:
    from ripe.atlas.cousteau import Probe
except:
    print("Could not import Probe",
        "\nPlease install ripe.atlas.cousteau with pip or apt-get.")
    askexit()

class depaddr:
    """Deprecated address"""
    def __init__(self, addr):
        self.addr = addr      #IPv6 address
        self.interface = None #Interface name
        self.life = 0         #Lifetime when deprecated (seconds)
        self.then = 0         #System time when deprecated (seconds)
    
def askexit():
    """Get me outa here"""
    input("Press Enter to Exit.")
    exit()

def refresh_guas():
    """Refresh GUA list"""
    global guas
    guas = []

    # This code is o/s dependent

    if windows:              
        _addrinfo = socket.getaddrinfo(socket.gethostname(),0)
        for _af,_temp1,_temp2,_temp3,_addr in _addrinfo:
            if _af == socket.AF_INET6:
                _addr,_temp,_temp,_zid = _addr  #get first item from tuple
                
                if not '%' in _addr:
                    _loc = ipaddress.IPv6Address(_addr)
                    # Now test for GUA address
                    if _loc.is_global:
                        guas.append(_loc)  # save GUA
            
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
                            # Now test for GUA
                            if _loc.is_global:
                                guas.append(_loc)  # save GUA

def tryping(a):
    """Try ping from specified source address; return success/fail Boolean"""
    # This works by synthesising ping commands and parsing the
    # text replies. It's very sensitive to any changes in ping
    # implementations.
    success = True
    if windows:
        cmd = "ping -6 -n 4 -S "+str(a)+" "+target
        #print("CMD=", cmd)
        for l in os.popen(cmd):
            if "Received = 0" in l or "could not find host" in l:
                #this source address fails
                success = False
    elif linux:
        #Linux
        cmd = "ping -6 -c 4 -I "+str(a)+" "+target
        #print("CMD=", cmd)
        for l in os.popen(cmd):
            if " 0 received" in l or "not known" in l:
                #this source address fails
                success = False
    else:
        #Other POSIX TBD
        success = False
        
    return success


def getlife(a):
    """Return lifetime of an address in seconds, and its interface name"""
    # This works by parsing the text replies to system commands.
    # It's very sensitive to any changes in o/s details.
    if windows:
        for l in os.popen("netsh int ipv6 show addr"):
            if l.startswith("Interface "):
                _,ll = l.split(" ", maxsplit=1)
                iname,_ = ll.split(":") 
            if str(a) in l:
                h = 0
                m = 0
                s = 0
                life = l.split()[2]
                if life == "infinite":
                    return(-1, iname)
                if "h" in life:
                    h,life = life.split("h")
                    h = int(h)
                if "m" in life:
                    m,life = life.split("m")
                    m = int(m)
                if "s" in life:
                    s,_ = life.split("s")
                    s = int(s)
                return((3600*h + 60*m + s), iname)
    elif linux:
        found = False
        for l in os.popen("ip addr"):
            if found:
                if "preferred_lft forever" in l:
                    return(-1, iname)
                else:
                    _,life = l.split("preferred_lft ")
                    return(int(life[:-4]), iname)
            if l[0].isdigit():
                _,iname,_ = l.split(":", maxsplit=2)
                iname = iname.strip()
            found = str(a) in l
    else:
        #Other POSIX TBD
        return(0, None)
            
print("=====================================================")
print("This program runs indefinitely to find failing IPv6")
print("source addresses and deprecate them.")
print("Probing interval is never less than 1 minute.")
print("=====================================================")

print("This is experimental software that might disturb network access.")
_l = input("Continue? Y/N: ")
if _l:
    if _l[0] != "Y" and _l[0] != "y":
        exit()
else:
    exit()

testing = False
_l = input("Simulate random failures? Y/N: ")
if _l:
    if _l[0] == "Y" or _l[0] == "y":
        testing = True


my_os = sys.platform
windows = False
linux = False

if my_os == "win32":
    print("You are running on Windows.")
    windows = True
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Cannot run without Administrator privilege.")
        askexit()
    print("Note: on Windows, anomalies have been seen when ULAs active.")
else:
    if my_os not in ("linux", "linux2"):
        print("Platform", my_os, "not yet supported.")
        askexit()
    try:
        print("You are running on Linux.")
        linux = True
        import netifaces     
        if os.geteuid() != 0:
            print("Cannot run without sudo privilege.")
            askexit()
            
    except:
        print("Could not import netifaces",
              "\nPlease install netifaces with pip or apt-get.")
        askexit()
        
prng = random.SystemRandom()
target = None
_l = input("Probe target's FQDN or IPv6 address?\n(press ENTER for default): ")
if _l:
    target = _l
    if not tryping("::"):
        print(_l, "is not pingable.")
        target = None

if not target:
    print("Choosing probe target; may take a minute...")
    for i in range(1,10):
        tryp = prng.randint(6000, 7200)
        probe = Probe(id=tryp)
        if probe.is_anchor and probe.status == 'Connected' and probe.address_v6:
            target = probe.address_v6
            if tryping("::"):
                break      
if not target:
    target = "www.google.com" #ultimate fallback only
print("Using", target, "as probe target") 

guas = [] # list of guas most recently found
deps = [] # list of currently deprecated addresses
loops = 1 # could be used for testing

while True:
    refresh_guas()
    if not (len(guas) + len(deps)):
        print("No globally routable IPv6 address found.")
        wait = 600 #10 minutes

    else:
        if len(guas) == 1:
            print("Only one globally routable IPv6 address found.")
        else:
            print(len(guas), "globally routable IPv6 addresses found.")
        print(guas)

        teston = False
        for a in guas:
            pingfail = not tryping(a)

            if testing and prng.randint(1, 4) == 3:  # fail at random
                teston = True
                pingfail = True
                
            if pingfail:
                print("Attempting to deprecate", a)
                # This works by synthesising system commands.
                # It's very sensitive to any changes in o/s details.
                da = depaddr(a)
                da.life, da.interface = getlife(a)
                da.then = int(time.monotonic())                    
                deps.append(da)
                if windows:
                    cmd = "netsh int ipv6 set address "+da.interface+" "+str(a)+" preferredlifetime=0 store=active" 
                elif linux:
                    cmd = "ip -6 addr change "+str(a)+"/64 dev "+da.interface+" preferred_lft 0"
                else:
                    cmd = "#unsupported o/s" 
                print("CMD=", cmd)
                for l in os.popen(cmd):
                    print(l)
            else:
                print("Ping OK from",str(a))
                
        #Test those previously deprecated and reactivate if OK
        i = 0  #manual loop count to allow for deletion
        while i < len(deps):
            if teston:
                teston = False #skip this time round so that test works
                break
            a = deps[i].addr
            print("Trying deprecated", a)
            if tryping(a):
                #Working again, need to restore it
                print("Attempting to revive", a)
                # This works by synthesising system commands.
                # It's very sensitive to any changes in o/s details.
                if windows:
                    if deps[i].life == -1:
                        life = "infinite"
                    else:
                        life = str(max(deps[i].life-(int(time.monotonic())-deps[i].then), 1000))
                    cmd = "netsh int ipv6 set address "+deps[i].interface+" "+str(a)+" preferredlifetime="+str(life)+" store=active"
                elif linux:
                    if deps[i].life == -1:
                        life = "forever"
                    else:
                        life = str(max(deps[i].life-(int(time.monotonic())-deps[i].then), 1000))
                    cmd = "ip -6 addr change "+str(a)+"/64 dev "+deps[i].interface+" preferred_lft "+life
                else:
                    cmd = "#unsupported o/s"
                    
                del(deps[i])
                i -= 1   #offset loop count
                print("CMD=", cmd)
                for l in os.popen(cmd):
                    print(l)
            i += 1
                    
        wait = 60 #1 minute

    print("Waiting", wait, "seconds")
    loops += 1
    time.sleep(wait)





    


    
