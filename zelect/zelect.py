#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Synthesize the mDNS name 'test.local' for any complete IPv6 link-local address entered by the user"""

########################################################
#
# Released under the BSD "Revised" License as follows:
#                                                     
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
########################################################

# Version: 20240311 - original

import socket
import ipaddress
import struct
import time
import os
import threading
windows = (os.name == "nt")
if not windows:
    print("Warning - this program doesn't do what it should on Linux.")
    try:
        from scapy.all import *
    except:
        print("Need scapy - pip install scapy")
        time.sleep(10)
        exit()
    import sys
    if 'idlelib' in sys.modules:
        print("Sorry, this program will not work when running under IDLE.")
        exit()
    del sys

## Here is the layout of the unsolicited mDNS response message that will be sent:
##
##0000 # ID = 0
##8000 # flags (Reply only)
##0000 # no of questions  
##0001 # no of answers
##0000 # no of authority RRs
##0000 # no of additional RRs
##
##04         # 4 bytes   ----> start of answer and start of name
##74657374   # 'test'
##05         # 5 more bytes
##6c6f63616c # 'local'
##00         # no more bytes
##001c       # type (AAAA)
##0001       # class
##0000012c   # TTL (5 minutes)
##0010       # RD length (16)
##fe800000000000000000000000000001  # packed target address (16 bytes)

## And here is the response message in hexadecimal, without the target address
mdns_response = "0000800000000001000000000474657374056c6f63616c00001c00010000012c0010"
#### Or with cache-flush set(doesn't change anything)
##mdns_response = "0000800000000001000000000474657374056c6f63616c00001c80010000012c0010"

mdns_addr = 'ff02::fb'
mdns_port = 5353

zzzz = []    # list of valid zone indexes (only needed for Windows)

def build_zones():
    """Build list of valid zone indexes for Windows"""
    global zzzz
    if windows:
        #Windows - build current list of valid zones
        zzzz = []
        _addrinfo = socket.getaddrinfo(socket.gethostname(),0)
        for _af,_temp1,_temp2,_temp3,_addr in _addrinfo:
            if _af == socket.AF_INET6:
                _addr,_temp,_temp,_zid = _addr  #get first item from tuple
                if '%' in _addr:
                    #this applies on Windows for Python before 3.7
                    _addr,_zid = _addr.split('%') #strip any Zone ID
                    _zid = int(_zid)
                if _zid and not _zid in zzzz:
                    zzzz.append(_zid)

class sender(threading.Thread):
    """Send the mDNS response repeatedly"""
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        while ready:
            # Send an unsolicited mDNS response
            # Repeat to bypass cache timeout
            if windows:
                try:
                    mcsock.sendto(msg,0,(mdns_addr, mdns_port))
                except Exception as e:
                    print("Socket send error: ", e)
            else:
                # The POSIX branch, using scapy. This doesn't work as intended on Linux.
                pkt = IPv6(src=scapy_src,dst=mdns_addr,hlim=255)/UDP(sport=mdns_port,dport=mdns_port)/Raw(load=msg)
                #or, for use with sendp():
                #pkt = Ether(dst='33:33:00:00:00:fb')/IPv6 ...
                #or, to forge the source MAC address, with catastrophic side effects:
                #pkt = Ether(src='e8:03:9a:3c:67:7a',dst='33:33:00:00:00:fb')/IPv6 ...
                
                try:
                    send(pkt, iface=zid, verbose=0)
                    # Wireshark results suggested that iface doesn't work properly on Linux.
                    # Also it seemed that avahi-daemon doesn't receive the host's own
                    # multicasts, and doesn't apply the mDNS response even
                    # when sent by another machine (and also and doesn't obey 
                    # avahi-publish-address correctly).
                except Exception as e:
                    print("Scapy send error: ", e)
            time.sleep(1)

print("This is zelect, which abuses mDNS to synthesize the DNS\n\
name 'test.local' for any complete IPv6 link-local address\n\
entered by the user.\n\nUse with care!\n\n")

# Outer loop for address input
while True:
    ready = False

    # Input dialogue loop

    while not ready:
        target = "fe80::2e3a:fdff:fea4:dde7%7" ## or any other test address you like
        inp = input("Enter IPv6 link-local address%interface: ")

        if inp:
            target = inp
        else:
            print("Blank input - using test value", target)
        try:
            addr, zid = target.split("%")
            scapy_src = addr
            addr = ipaddress.IPv6Address(addr)
            if not addr.is_link_local:
                print("Not link-local, please try again")
                continue
            addr = addr.packed
        except:
            print("Invalid format, please try again")
            continue

        try:
            if windows:
                zix = eval(zid)  # windows shortcut
                build_zones()    # this list needs to be fresh
                if not (zix in zzzz):
                    0/0
##                # to use scapy on Windows...                   
##                zid = str(dev_from_index(zix))
##                print("scapy iface:", zid)
            else: # assume POSIX
                zix = socket.if_nametoindex(zid)
        except:
            print("Invalid interface identifier, please try again.")
            continue
        ready = True

    # Build mDNS response message
    
    msg = bytes.fromhex(mdns_response) + addr

    if windows:
        # Open a socket to send mDNS multicasts
        mcsock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        mcsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mcsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, struct.pack('@I', zix))
        mcsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)
        mcsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)  

    # Start sending the mDNS unsolicited response
    sender().start()

    print("Sending mDNS unsolicited response.")
    print("'test.local' should now resolve as", target)

    # Wait until user wants out
    input("Press enter to stop: ")
    print("Stopping...")
    ready = False # signals the sender to stop
    time.sleep(2) # wait for sender to exit and mDNS cache to clear
    print("'test.local' should no longer resolve.")
    t = input("R to restart, anything else to exit: ")
    if t.lower().startswith("r"):
        if windows:
            try:
                mcsock.close()
            except Exception as e:
                print("Socket close error: ", e)
        # Start again
    else:
        break
        # Exit
