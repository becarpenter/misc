#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Demo of default zone sending behaviour"""
import socket
import os

def tryz(zone):
    """Send a packet to {target, zone}"""
    try:
        print("Trying zone", zone)
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.connect((target, 12345, 0, zone))
        if windows:
            #sendmsg doesn't exist on Windows
            result = sock.sendto(msg_bytes,0,(target, 12345))
        else:
            result = sock.sendmsg([msg_bytes])
        sock.close()
        return("Result: "+str(result)+" bytes sent\n")

    except Exception as e:
        sock.close()
        return(str(e)+"\n")

def cmd(command):
    """Execute system command"""
    do_cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _out, _err = do_cmd.communicate()
    if _err:
        print(_err.decode('utf-8').strip())
        return(None)
    if _out:
        _out = _out.decode('utf-8').strip()
        return(_out)

print("This program shows whether a host does or does not support")
print("a default zone index of zero when sending to a link-local")
print("IPv6 address. For completeness it also sends to a valid zone")
print("and to an invalid zone.\n")

msg_bytes = bytes(b"Test")
windows = (os.name=="nt")

# find a valid  address and zone
if windows:
    #netifaces is problematic on windows
    import subprocess
    info = cmd("ipconfig")
    
    try:
        if "Default Gateway" in info:
            _, info = info.split("Default Gateway", maxsplit=1)
            _, addr = info.split("fe80::", maxsplit=1)
            addr, tail = addr.split("%", maxsplit=1)
            target = "fe80::"+addr
            zone, _ = tail.split("\n", maxsplit=1)
            zone = int(zone)
        else:
            0/0
    except:
        input("Cannot find IPv6 default gateway...")
        exit()            
else:
    import netifaces
    target, zone = netifaces.gateways()['default'][netifaces.AF_INET6]
    zone = socket.if_nametoindex(zone)

print("Target is",target, "and its zone index is",zone,"\n")

# run tests

print(tryz(zone))
print(tryz(99))
print(tryz(0))
input("OK? ")



        




