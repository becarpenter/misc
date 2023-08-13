#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""########################################################
########################################################
#                                                     
# ULA evaluation (ulation.py)     
#                                                                                                        
# This program asesses the presence of Unique Local
# Addresses (ULAs, RFC4193) in a host and if present,
# checks various properties and reports on them.
#
# It's intended to work on Windows or POSIX-compliant
# systems. This version uses shell commands, not the
# socket interface.
#
# On Windows, we use socket.getaddrinfo to find addresses
#
# On Linux, we use netifaces to find addresses
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

#Version 2023-08-13

import os
import ctypes
import struct
import sys
import socket
import ipaddress
import subprocess
import time
import dns.resolver
import random # used for testing
try:
    from ripe.atlas.cousteau import Probe
    atlas = True
except:
    print("Could not import Probe",
        "\nPlease install ripe.atlas.cousteau with pip or apt-get.",
         "\nFor now we'll manage without")
    atlas = False
    


try:
    dns.resolver.resolve
    #must be modern library
    my_resolve = dns.resolver.resolve
except:
    #must be old library
    my_resolve = dns.resolver.query

def resolve(n,q):
    """Resolve a single domain and return the RR"""
    #grasp.tprint(resolver)
    try:
        #print("Resolving",n,q)
        a = my_resolve(n,q)
        #print("Got",a)
        return a
    except Exception as ex:
        #print("DNS resolver error:", ex)
        return []
   
def askexit():
    """Get me outa here"""
    input("\nPress Enter to Exit.")
    exit()

def rand32():
    """Make 32 random bits"""
    return struct.pack('!L', prng.randint(0, 2147483647))

def rand24():
    """Make 24 random bits"""
    return struct.pack('!L', prng.randint(0, 8388607))[1:]

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

def is_ula(a):
    """Test for ULA"""
    return(str(a).startswith("fd"))

def refresh_addrl():
    """Refresh address list"""
    global addrl, ipv6
    addrl = []

    # This code is o/s dependent

    if windows:              
        _addrinfo = socket.getaddrinfo(socket.gethostname(),0)
        for _af,_temp1,_temp2,_temp3,_addr in _addrinfo:
            if _af == socket.AF_INET6:
                _addr,_temp,_temp,_zid = _addr  #get first item from tuple
                
                if not '%' in _addr:
                    _loc = ipaddress.IPv6Address(_addr)
                    # Now test for GUA or ULA
                    if _loc.is_global or is_ula(_loc):
                        addrl.append(_loc)  # save address
                        ipv6 = True
            elif _af == socket.AF_INET:
                _addr,_temp = _addr  #get first item from tuple
                _loc = ipaddress.IPv4Address(_addr)
                addrl.append(_loc)  # save address
            
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
                            # Now test for GUA or ULA
                            if _loc.is_global or is_ula(_loc):
                                addrl.append(_loc)  # save address
                                ipv6 = True
            elif netifaces.AF_INET in config.keys():
                for link in config[netifaces.AF_INET]:
                    if 'addr' in link.keys():
                        _addr = link['addr']
                        _loc = ipaddress.IPv4Address(_addr)
                        addrl.append(_loc)  # save address

def tryping(sa, da):
    """Try ping from specified source address; return 'OK' or error string"""
    # This works by synthesising ping commands and parsing the
    # text replies. It's very sensitive to any changes in ping
    # implementations.
    result = "OK"
    if windows:
        cmd = "ping -6 -n 2 -S "+sa+" "+da
        #print("CMD=", cmd)
        for l in os.popen(cmd):
            if "General failure" in l:
                return("No route")
            elif "could not find host" in l:
                return("No DNS")
            elif "Received = 0" in l:
                return("No reply")
    elif linux:
        #Linux
        cmd = "ping -6 -c 2 -I "+sa+" "+da
        #print("CMD=", cmd)
        for l in os.popen(cmd):
            if "not known" in l:
                return("No DNS")
            elif "Beyond scope" in l:
                return("No route")
            elif " 0 received" in l:
                return("No reply")
    else:
        #Other POSIX TBD
        result = "TBD"
        
    return result


#Not currently using the following function, but maybe one day...
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
print("This program evaluates the presence and configuration")
print("of IPv6 Unique Local Addresses (ULAs)")
print("=====================================================")

my_os = sys.platform
windows = False
linux = False

if my_os == "win32":
    print("You are running on Windows.")
    windows = True
##    if not ctypes.windll.shell32.IsUserAnAdmin():
##        print("Cannot run without Administrator privilege.")
##        askexit()
else:
    if my_os not in ("linux", "linux2"):
        print("Platform", my_os, "not yet supported.")
        askexit()
    try:
        print("You are running on Linux.")
        linux = True
        import netifaces     
##        if os.geteuid() != 0:
##            print("Cannot run without sudo privilege.")
##            askexit()
            
    except:
        print("Could not import netifaces",
              "\nPlease install netifaces with pip or apt-get.")
        askexit()

# Get address list

ipv6 = False
addrl = []
refresh_addrl()
if not ipv6:
    print("No routeable IPv6 address found. Cannot continue analysis.")
    askexit()
    
ulas = 0

print("\nYour current IP addresses:")
for a in addrl:
    ulas += int(is_ula(a))
    print("   ", a)
if not ulas:
    print("No ULA found - is this intentional? Cannot continue analysis.")
    askexit()

# Show current precedence table
print("\nCurrent RFC3484/6724 table:")
if windows:
    wincmd("netsh interface ipv6 show prefixpolicies")
elif linux:
    shcmd("cat /etc/gai.conf")


fqdn = socket.getfqdn()
print("\nYour DNS name is", fqdn)
RR = resolve(fqdn, "AAAA")
if not RR:
    print("No AAAA record found in local DNS")
else:
    print(RR)

# Set up a random number generator
prng = random.SystemRandom()

# Select an IPv6 GUA probe target - normally a random ATLAS probe
target = None
_l = input("\nChoose a probe target (FQDN or IPv6 address)\n(press ENTER for default): ")
if _l:
    target = _l
    if not tryping("::", target) == "OK":
        print(_l, "is not pingable.")
        target = None

if (not target) and atlas:
    print("Choosing probe target; may take a minute...")
    for i in range(1,10):
        tryp = prng.randint(6000, 7200)
        probe = Probe(id=tryp)
        if probe.is_anchor and probe.status == 'Connected' and probe.address_v6:
            target = probe.address_v6
            if tryping("::", target) == "OK":
                break      
if not target:
    target = "www.google.com" #ultimate fallback only
print("Using", target, "as global IPv6 probe target")

# Create two random ULA targets
ula1 = bytes.fromhex('fd')+rand24()+rand32()+rand32()+rand32()
ula2 = bytes.fromhex('fd')+rand24()+rand32()+rand32()+rand32()
ula1 = ipaddress.IPv6Address(ula1)
ula2 = ipaddress.IPv6Address(ula2)

print("Using",ula1,"and", ula2, "as ULA probe targets")

for a in addrl:
    if is_ula(a):
        
        # check ULA->ULA does not escape
        print("\nChecking ULA->ULA routing from", a)
        result = tryping(str(a), str(ula1))
        if result == "OK":
            #highly unlikely but let's just check...
            result = tryping(str(a), str(ula2))
            if result == "OK":
                print("Please check 2nd law of thermodynamics.")
                askexit()
        if result == "No route":
            print("Expected result: ULA cannot be routed externally")
        elif result == "No reply":
            print("!Undesirable result!: ULA appears to have been routed to external ULA")

        # check ULA->GUA does not escape
        print("\nChecking ULA->GUA routing from", a)
        result = tryping(str(a), target)
        if result == "OK":
            print("Surprising success: is NPTv6 or NAT66 installed?")
        elif result == "No route":
            print("Expected result: ULA cannot be routed externally")
        elif result == "No reply":
            print("!Undesirable result!: ULA appears to have been routed to external GUA")
        
askexit()

