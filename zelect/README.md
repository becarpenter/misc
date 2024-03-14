# zelect

## Windows 10

_zelect_ is a Python3 program that abuses mDNS to synthesize the DNS
name _test.local_ for any complete IPv6 link-local address (LLA)
entered by the user in a simple command line interface
(which incidentally conforms to [draft-carpenter-6man-zone-ui](https://datatracker.ietf.org/doc/draft-carpenter-6man-zone-ui/)).
This program is a hack inspired by [draft-schinazi-httpbis-link-local-uri-bcp](https://datatracker.ietf.org/doc/draft-schinazi-httpbis-link-local-uri-bcp/).

At present it only works properly on Windows 10, where it can use
a regular socket call to send a synthetic unsolicited mDNS
response message. While it is running, the user can perform
`ping test.local` and it goes to the LLA supplied.

More interestingly, all the browsers tested so far on Windows 10 support
http://test.local or https://test.local correctly - that is, they
attempt an HTTP(S) connection to the target LLA. Typically it fails
with a reset, which is the expected result.

When you tell _zelect_ to stop (or it crashes), _test.local_ reverts
to not working.

This was tested on Windows 10 22H2 (build 19045.4046). No promises
for any other Windows version.

An unintended side effect is that while _zelect_ is running, all other
Windows hosts on the same LAN will also see the _test.local_ name
in mDNS.

Obviously, this is a hack, you use it at your own risk.

## Linux (a tale of woe)

It _ought_ to work on Linux, but it doesn't. The code is in there, and
anyone who can figure out how to make it work is owed a beer or an ice
cream (offer applies in Auckland only). On Linux, the _avahi_ mDNS
implementation only accepts mDNS responses from port 5353. However,
even that doesn't work because it seems that avahi
ignores multicasts from its own host (`IPPROTO_IPV6 IPV6_MULTICAST_LOOP 0`,
apparently). So even fabricating mDNS packets with _scapy_ doesn't work.

Additionally, while _zelect_ is running using _scapy_ on Linux, 
Windows hosts on the same LAN _will_ see the `test.local` name
in mDNS. In other words, the Linux _scapy_ code is working, but Linux
isn't listening.

Even sending such fabricated packets from another machine didn't work
at first. It turns out that there is a critical setting in
`/etc/nsswitch.conf`. There __MUST__ be a line like this:

```
hosts:      files mdns [NOTFOUND=return] resolve [!UNAVAIL=return] dns
```
Note, it's `mdns` __NOT__ `mdns4`, which seems to be widely used, but
prevents IPv6 resolution from working at all.

However, with packets fabricated using _scapy_ on Windows, we then find
that on Linux `ping test.local` works. 

(This is done by the experimental version, 'zelect-try.py'.)

Also, on Firefox, http://test.local works too - it gets `connection reset`
which is the expected result.

There are several gotchas:

1. There is a very long delay (since apparently it attempts to
resolve 'test.local' for IPv4, which has to time out first).

2. Neither `ping6 test.local` nor `ping -6 test.local` works
properly. They both resolve the name but then fail with a
sendmsg() 'invalid argument' error, which indicates that they
don't pick up the interface number from mDNS. It seems that
these variants use a different and buggy code path than plain
`ping test.local`.

3. Chrome can resolve the name but the connection fails
with `ERR_INVALID_ARGUMENT`, exactly the same error as with
`ping6`.

4. Avahi doesn't forget the mDNS record after 1 second, as
Windows does. However, it does respect the TTL and therefore
deletes the 'test.local' name after 5 minutes.

Note that _avahi-publish-address_ cannot possibly work for LLAs, because it
uses _inet_pton()_ which doesn't understand zone identifiers at all.

Putting a link local address in the `/etc/avahi/hosts` file doesn't work
either, for the same reason - you can't specify the interface name.
(There are perhaps some corner cases
where it might work, but if a host has several LAN interfaces
active, it definitely won't work.)


## Example run on Windows

Download _zelect.py_ and double click on the file, assuming you
have Python 3 and the standard libraries installed. (Tested on
Python 3.11.)

```
This is zelect, which abuses mDNS to synthesize the DNS
name 'test.local' for any complete IPv6 link-local address
entered by the user.

Use with care!


Enter IPv6 link-local address%interface: fe80::2e3a:fdff:fea4:dde7%7
Invalid interface identifier, please try again.
Enter IPv6 link-local address%interface: fe80::2e3a:fdff:fea4:dde7%24
Sending mDNS unsolicited response.
'test.local' should now resolve as fe80::2e3a:fdff:fea4:dde7%24
Press enter to stop:
```

At this point, at the Windows prompt in another window, we can test it out:

```
C:\WINDOWS\system32>ping test.local

Pinging test.local [fe80::2e3a:fdff:fea4:dde7%24] with 32 bytes of data:
Reply from fe80::2e3a:fdff:fea4:dde7%24: time=1ms
Reply from fe80::2e3a:fdff:fea4:dde7%24: time=1ms
Reply from fe80::2e3a:fdff:fea4:dde7%24: time=1ms

Ping statistics for fe80::2e3a:fdff:fea4:dde7%24:
    Packets: Sent = 3, Received = 3, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 1ms, Maximum = 1ms, Average = 1ms
```
And then press Enter in _zelect_'s window:

``` 
Stopping...
'test.local' should no longer resolve.
R to restart, anything else to exit: r
Enter IPv6 link-local address%interface: 
```
