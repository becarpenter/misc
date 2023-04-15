# whenmail

Some plots of when IETFers send email, on an hourly or daily basis. These plots cover three MBOX files on separate topics: differentiated services, IPv6 in general, and IPv6 deployment issues. There are plots for the senders' local time zone and for UTC in each case.

This doesn't cover *all* email; it covers all the email I happen to have kept on these topics. The code should work on any MBOX-format file.

No emails that I personally** sent were counted, and only emails where the string "ietf" (or "IETF") appears in the To: or Cc: (or CC:) fields were counted.

ADDED in April 2023: The latest four graphs are based on _all_ of the last year's traffic from the IETF archive for the 6MAN WG. The code has also been fixed because it was missing some messages previously (MBOX format is not all that clean!), and filtering on a sender is now optional.

The code is here but there is no warranty of any kind; do what you want with it at your own risk.

** or anyone else called Brian, for reasons of lazy programming.
