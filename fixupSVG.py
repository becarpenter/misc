#This Python tool performs a heuristic trim of an SVG file.
#It's intended for use before applying the IETF svgcheck
#tool that checks and fixes up an SVG file for use in RFCs
#according to RFC7996.

#It's hacked together for convenient use on my Windows
#setup, not as part of a toolchain, and it uses simple
#pattern matching in the SVG, rather than a full parse.

#This tool does several things:
#
#1. Any <?xml ...> or <!DOCTYPE ...> declarations are removed,
#   because they seem to upset the IETF toolchain.
#
#2. Colour or grey-scale fills and strokes are changed to black
#   or white. Lighter fills are changed to white, and darker 
#   ones to black. In many cases, this will be helpful for 
#   diagrams prepared for another purpose but used in an RFC.
#   If the result is not OK, it will be necessary to fix the
#   the offending colors in the original drawing tool.
#
#3. Remove 'stroke="none"' and 'stroke:none'
#   because they seem to upset the IETF toolchain.
#
#4. Remove 'width' and 'height' from 'viewbox'.
#   This assists proper scaling when viewing the final
#   html file with most browsers.
#
#5. NOT fixed up here: RFC7996 disallows fill using a URL
#   for the pattern; I also have a hack that allows this
#   if and only if the URL points to an embedded pattern
#   (embedded in the SVG file itself, i.e 'url(#xxxx)'

import fileinput
import time

def fix_rgb(l):
    """Force color to monochrome"""
    #This function calls itself recursively to fix the whole line

    threshold = 381 #arbitrary choice for black/white threshold
    
    if 'fill="rgb(' in l or 'stroke="rgb(' in l:
        #rgb color code
        if 'fill="rgb(' in l:
            element = 'fill'
        else:
            element = 'stroke'
        l1,l2 = l.split(element+'="rgb(',1)
        triple,l3 = l2.split(')"',1)
        if '%' in triple:
            #percentage rgb values
            t = eval(triple.replace('%',''))
            shade = int(t[0]*255/100) + int(t[1]*255/100) + int(t[2]*255/100)            
        else:
            #decimal rgb values
            shade = sum(eval(triple))
        if shade > threshold:
            #make it white
            lout = l1 + element+'="white"' +l3
        else:
            #make it black
            lout = l1 + element+'="black"' +l3
        print("Fixed rgb")
        return(fix_rgb(lout))
    
    elif 'fill="#' in l or 'stroke="#' in l:
        #hexadecimal color code
        if 'fill="#' in l:
            element = 'fill'
        else:
            element = 'stroke'
        l1,l2 = l.split(element+'="#',1)
        code = l2[:6] #just the 6 hex digits
        l3 = l2[7:]   #not including the closing "
        shade = int(code[0:2],16) + int(code[2:4],16) + int(code[4:6],16)
        if shade > threshold:
            #make it white
            lout = l1 + element+'="white"' +l3
        else:
            #make it black
            lout = l1 + element+'="black"' +l3
        print("Fixed #color")
        return(fix_rgb(lout))
    
    elif 'fill:#' in l or 'stroke:#' in l:
        #hexadecimal color code from Inkscape
        if 'fill:#' in l:
            element = 'fill'
        else:
            element = 'stroke'
        l1,l2 = l.split(element+':#',1)
        code = l2[:6]  #just the 6 hex digits
        l3 = l2[6:]    #there is no closing "
        shade = int(code[0:2],16) + int(code[2:4],16) + int(code[4:6],16)
        if shade > threshold:
            #make it white
            lout = l1 + element+':white' +l3
        else:
            #make it black
            lout = l1 + element+':black' +l3
        print("Fixed :#color")
        return(fix_rgb(lout))
        
    else:
        return(l)

def nostroke(l):
    """Remove stroke="none"""
    #This function calls itself recursively to fix the whole line
    if 'stroke="none"' in l:
        l1,l2 = l.split('stroke="none"',1)
        print('Removed stroke="none"')
        return(nostroke(l1+l2))
    elif 'stroke:none' in l:
        l1,l2 = l.split('stroke:none',1)
        print('Removed stroke:none')
        return(nostroke(l1+l2))
    else:
        return(l)

def nowh(l):
    """Remove width and height to allow scaling"""
    if 'viewBox' in l:
        print("Seen viewbox")
        if ' width="' in l:
            l1,l2 = l.split(' width="',1)
            _,l3 = l2.split('"',1)
            lout= l1 + l3
            print("Removed width")
        else:
            lout = l
        if ' height="' in lout:
            l1,l2 = lout.split(' height="',1)
            _,l3 = l2.split('"',1)
            lout= l1 + l3
            print("Removed height")
        return(lout)
    else:
        return(l)

#This is pure laziness because standard output
#just isn't convenient on Windows
fout = 'C:/brian/docs/temp/fixed.svg'
trimmed = open(fout, "w")

print('Fixing up standard input file')
for line in fileinput.input():
    if (not '<?xml' in line) and (not '<!DOCTYPE' in line):
        #line is useful
        l = fix_rgb(line)
        l = nostroke(l)
        l = nowh(l)
        trimmed.write(l)
        #Yes, OK, trimmed.write(nowh(nostroke(fix_rgb(line)))) would work too.
trimmed.close()
print('Fixed file is', fout)

#This gives time to read the outputs, because on Windows
#your window just goes away on exit.
time.sleep(10)


    
