# whenmail

Some plots of when IETFers send email, on an hourly or daily basis. The older plots cover three MBOX files on separate topics: differentiated services, IPv6 in general, and IPv6 deployment issues. There are plots for the senders' local time zone and for UTC in each case.

This doesn't cover *all* email; it covers all the email I happen to have kept on these topics. The code should work on any MBOX-format file.

No emails that I personally** sent were counted, and only emails where the string "ietf" (or "IETF") appears in the To: or Cc: (or CC:) fields were counted.

ADDED in April 2023: The latest eight graphs are based on _all_ of the last year's traffic from the IETF archives for the 6MAN and QUIC WGs. The code has also been fixed because it was missing some messages previously (MBOX format is not all that clean!), and filtering on a sender is now optional.

To use this with the IETF email archive, you need to select and export a set of emails. Quoting Robert Sparks:
```
Login to mailarchive.ietf.org

Browse to a list - restrict the view with a search (date based perhaps) 
so that you have < 5000 results.

Hit export in the search bar.

Choose Mbox.
```
Then you'll need to detar the files received (tar -xzvf XXXX.tar.gz on Linux or Cygwin) and launch mdates.py .

The code is here but there is no warranty of any kind; do what you want with it at your own risk.

** or anyone else called Brian, for reasons of lazy programming.
