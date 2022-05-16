#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python wrapper for getaddrinfo() to prefer ULA when appropriate.
Afte importing socket, from gai_wrap import getaddrinfo"""

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

import sys
import socket
import ipaddress
import time
import threading

#work-around for Python system error
try:
    socket.IPPROTO_IPV6
except:
    socket.IPPROTO_IPV6 = 41

from socket import getaddrinfo as gai

def _is_ula(a):
    """Test for ULA"""
    return (a.is_private and not a.is_link_local
             and not a.is_loopback
             and not a.is_unspecified)

def _save_ula(a):
    """If a is ULA, save prefix"""
    global _ulaps
    if _is_ula(a):
        a = ipaddress.IPv6Address(a.packed[:6]+bytes.fromhex('00000000000000000000'))
        if not a in _ulaps:
            _ulaps.append(a)
            

_my_os = sys.platform

if _my_os != "win32":
    import netifaces

_ulaps = []  #start with empty list of ULA prefixes
_expire = 0  #int(time.monotonic()) when we consider ULA info stale
_ula_lock = threading.Lock()
_ULA_LIFE = 60 #consider ULA info is stale after this many seconds


def _find_ulaps():
    """Refresh list of active ULA prefixes if expired"""
    #thread safe within this Python instance
    global _ula_lock, _ulaps, _expire
    _ula_lock.acquire()
    if int(time.monotonic()) < _expire:
        _ula_lock.release()
        return
    _ulaps = []
    if _my_os == "win32":
        #Windows
              
        _addrinfo = socket.getaddrinfo(socket.gethostname(),0)
        for _af,_temp1,_temp2,_temp3,_addr in _addrinfo:
            if _af == socket.AF_INET6:
                _addr,_temp,_temp,_zid = _addr  #get first item from tuple
                
                if not '%' in _addr:
                    #save prefix if ULA
                    _save_ula(ipaddress.IPv6Address(_addr))

            
    else: #assume POSIX     
        ifs = netifaces.interfaces()
        for interface in ifs:
            config = netifaces.ifaddresses(interface)
            if netifaces.AF_INET6 in config.keys():
                for link in config[netifaces.AF_INET6]:
                    if 'addr' in link.keys():
                        _addr = link['addr']
                        if not '%' in _addr:
                            #save prefix if ULA
                            _save_ula(ipaddress.IPv6Address(_addr))
                                
    _expire = int(time.monotonic()) + _ULA_LIFE
    _ula_lock.release()
    return


def getaddrinfo(*whatever):
    "Enhances system getaddrinfo() to ensure correct handling of ULAs"
    global _ulaps
    _find_ulaps()
    results = gai(*whatever)
    for x in results:
        if x[0].name == "AF_INET6":
            a = ipaddress.IPv6Address(x[4][0])
            if _is_ula(a):
                #Found a ULA, should it be promoted?
                prefix = ipaddress.IPv6Address(a.packed[:6]+bytes.fromhex('00000000000000000000'))
                if prefix in _ulaps:
                    #Known prefix, reorder results
                    results.pop(results.index(x))
                    results.insert(0,x)        
    return results

    








    


    
