#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove duplicates and some bogons from extracted ABNF.
Use, copy and modify at your own risk."""

f = open("some.abnf","r")
fixed = []
for l in f.readlines():
    l = ' '.join(l.split()) # canonical whitespace
    # ignore blank lines
    if l:
        # heuristic: ignore raw $
        if '$' in l and not ("'$'" in l) and not ('"$"' in l):    
            print("Warning - ignoring", l)
        else:
            # restore whitespace before continuation char
            if l[0] == '/':
                l = ' '+l
            # keep line if not duplicate
            if not l in fixed:
                fixed.append(l)
f.close()

o = open("fixed.abnf","w")
for l in fixed:
    o.write(l+"\n")
o.close()
