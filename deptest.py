#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""########################################################
########################################################
#                                                     
# Source address deprecator tester (deptest.py)     
#                                                                                                        
# This program just tests whether source address
# deprecation has worked, by trying a connection
# and reporting the source address used. It's for
# use when testing deprecator.py
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

import os
import ctypes
import sys
import socket
import time                             

print("=====================================================")
print("This program runs indefinitely to report")
print("the source address chosen, every 15 s")
print("=====================================================")


my_os = sys.platform

if my_os == "win32":
    print("You are running on Windows.")

else:
    print("Assuming a POSIX-compliant operating system.")

target = "www.google.com"
port = 1021 #experimental port
print("Using", target, "as probe target")
ct = 1

while True:

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock_addr = socket.getaddrinfo(target, port, socket.AF_INET6, socket.SOCK_DGRAM)[0][4]
    sock.connect(sock_addr)
    me = sock.getsockname()
    print("Source is", me[0])
    sock.close()
    print("Waiting", ct)
    ct += 1
    time.sleep(15)





    


    
