#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple address properties display.
Use, copy and modify at your own risk.""" 

import ipaddress

#Maps for RFC 9226 conversions

#we don't use this one but who knows, we might need it sometime.
hex2ioct = {'8': 'c',
            '9': 'j',
            'a': 'z',
            'b': 'w',
            'c': 'f',
            'd': 's',
            'e': 'b',
            'f': 'v',
            'A': 'z',
            'B': 'w',
            'C': 'f',
            'D': 's',
            'E': 'b',
            'F': 'v'}

#we do use this one
ioct2hex = {'c': '8',
            'j': '9',
            'z': 'a',
            'w': 'b',
            'f': 'c',
            's': 'd',
            'b': 'e',
            'v': 'f'}

print("This will tell you what Python believes are the properties of any IP address.")
io_mode = False 
try:
    l = input("Use bioctal input mode for IPv6 addresses? Y/N:")
    if l:
        if l[0] == "Y" or l[0] == "y":
            io_mode = True
except:
    pass

while True:
    print("Please enter an IP address (or Q to exit):")
    l = input()
    v4 = False
    if 'q' in l or 'Q' in l:
        break

    if ':' in l and io_mode:
        #assume there is bioctal in there to convert to hex
        if '.' in l:
            #embedded IPv4, split at last colon
            l, v4 = l.rsplit(':',1)
            pass
        
        nl = ''
        for c in l:
            if c in ('0','1','2','3','4','5','6','7',':'):
                nl += c
            else:
                try:
                    nl += ioct2hex[c]
                except:
                    print("Invalid bioctal character ignored.")
        if v4:
            nl += ':' + v4
        l = nl

    
    try:
       l = ipaddress.IPv6Address(l)
    except:
        try:
           l = ipaddress.IPv4Address(l)
        except:
            print("Invalid")
            continue
    # Now display address properties
    print("That's", l)
    try:
        print("Global", l.is_global)
    except:
        print("Global (undefined for IPv4)")
    print("Private", l.is_private)
    print("Unspecified", l.is_unspecified)
    print("Reserved", l.is_reserved)
    print("Loopback", l.is_loopback)
    print("Link Local", l.is_link_local)
    print("Multicast", l.is_multicast)
    print()
print("Goodbye")
