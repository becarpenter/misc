#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Get and release an operating-system-wide lock. This works
by binding to a dummy socket."""

# Version: 2026-07-28 - original


########################################################
# Copyright (C) 2026 Brian E. Carpenter.                  
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

import socket
_sock = None     # Need this to be global
_port_used = 0   # Need this to be global

def get_lock(port=1021):
    """Get an operating-system lock to allow atomic operation.
By default it uses experimental port 1021. Any unused port number
will work, but all processes using the same lock must use the same
port number. Returns True if successful, otherwise False."""

    global _sock, _port_used

    if not _sock:
        _sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        _sock.bind(('::1', port)) # bind socket to loopback address
        #print("Obtained lock on port", port)
        _port_used = port
        return(True)
    except:
        #print("Could not get lock")
        return(False)

def release_lock(port=1021):
    """Release lock after atomic operation.
Returns True if successful, otherwise False."""

    global _sock, _port_used

    if port != _port_used:
        #print("Wrong port or already released")
        return(False)
    try:
        _sock.close()
        _sock=socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        #print("Released lock")
        _port_used = 0
        return(True)
    except Exception as e:
        print("Release failed:", e)
        return(False)


