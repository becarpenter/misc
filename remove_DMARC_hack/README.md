# Remove DMARC hack

This is a Thunderbird add-on that automatically changes any To:, Cc: or Bcc:
address on outgoing mail from the format

 - user=40example.com@dmarc.ietf.org

to

 - user@example.com

which looks nicer but, more importantly, avoids a pointless hop via the
IETF mail service, which does no good to anybody. You won't see the change
on-screen, but you will see it in the sent version of any affected email.

You can install this on Thunderbird by downloading the .xpi file from this
folder into a temporary location, and then using 

 - Preferences/Add-ons/__☼__/Install Add-on from File

(__☼__ is the little gear wheel symbol for further tools, and the exact
sequence may depend on your Thunderbird version.)

The source directory is here too (but the source code is also inside the .xpi file, which is really
a .zip file in disguise).

No warranty. Use at your own risk.

## What? What?

If you have no idea what this is all about, see [Enabling DMARC workaround code for all IETF/IRTF mailing lists](https://mailarchive.ietf.org/arch/msg/ietf/fZzt1mhBPqxG93y05ruGmMey9x4/)

I'm sorry it took me 5 years to get around to this.
