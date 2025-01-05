## Auto-configuration

One design goal for IPv6 was that it could be used "out of the box" in
an isolated network (referred to in the early 1990s as a "dentist's
office" network). Today, of course, this is a less likely scenario if
taken literally, but all the same, isolated network segments do indeed
arise. For this scenario, IPv6 has an elegant solution: when an IPv6
node first detects an active network interface, it will automatically
configure a link local address on that interface, such as
`fe80::a1b3:6d7a:3f65:dd13`. The interface identifier is a pseudo-random
64-bit number, normally fixed for a given interface. (In legacy
implementations, it may be derived from the interface's IEEE MAC
address, but this method is now deprecated.)

Link local addresses are usable only for operations on the same link.
The most common case is for traffic between a host and its first-hop
router. Another likely case is traffic between a host and local printer.
There is nothing to stop them being used for any other type of traffic
between local nodes, but they are useless *off* the given link and
should definitely never appear in DNS.

Further details are given in
[RFC 4862](https://www.rfc-editor.org/info/rfc4862). Also, we have
skipped an important issue that will be discussed later: duplicate
address detection.

When a node has configured a link local address, it then continues a
process known as SLAAC (pronounced 'slack') -- StateLess Address
AutoConfiguration -- in order to configure at least one routeable
address \[[RFC4862](https://www.rfc-editor.org/info/rfc4862)\].
Naturally, this can only happen on a link with an IPv6 router connected
to it. If there is no such router, only link local IPv6 operation is
possible. The first step, therefore, is router discovery. IPv6 routers
supporting SLAAC **MUST** listen to the link local all-routers multicast
address, defined as `ff02::2`. The new node will send a Router
Solicitation ICMPv6 message to that address. Each SLAAC router will
respond with a Router Advertisement (RA) ICMPv6 message to the new node
at its link local address. (RA messages are also sent periodically to
`ff02::1`, the link local all-nodes multicast address. This is important
to refresh information in all nodes.)

RA messages are quite complex and are defined in detail in
[RFC 4861](https://www.rfc-editor.org/info/rfc4861). They contain one
Prefix Information Option (PIO) for each routeable IPv6 prefix that they
can handle. A PIO naturally contains the prefix itself (theoretically of
any length; in practice normally 64 bits), some lifetime information,
and two flag bits known as L and A. L=1 signifies that the prefix is
indeed supported on the link concerned -- this is needed for on-link
determination as mentioned in the previous section. A=1 signifies that
the prefix may indeed be used for stateless address auto-configuration.
A PIO with A=L=0 signifies only that the router can act as the first hop
router for the prefix concerned
\[[RFC8028](https://www.rfc-editor.org/info/rfc8028)\]. For
auto-configuration, when a node receives a typical RA/PIO with A=L=1, it
configures an address for itself, and also records the fact the the
announced prefix is on-link. For example, if the prefix announced in the
PIO is `2001:db8:4006:80b::/64`, and the pre-defined interface
identifier for the interface concerned is `a1b3:6d7a:3f65:dd13`, the
node will configure the interface's new address as
`2001:db8:4006:80b:a1b3:6d7a:3f65:dd13`.

As mentioned in
[2. Addresses](../02.%20IPv6%20Basic%20Technology/Addresses.md), the
interface identifier should be pseudo-random to enhance privacy, except
in the case of public servers (thus a certain large company uses
identifiers like `face:b00c:0:25de`). For practical reasons, stable
identifiers are often preferred
\[[RFC8064](https://www.rfc-editor.org/info/rfc8064)\] but privacy is
better protected by temporary identifiers
\[[RFC8981](https://www.rfc-editor.org/info/rfc8981)\].

An important step in configuring either a link local address or a
routeable address is *Duplicate Address Detection* (DAD). Before a new
address is safe to use, the node first sends out a Neighbor Solicitation
for this address, as described in the previous section. If it receives a
Neighbor Advertisement in reply, there's a duplicate, and the new
address must be abandoned. The Neighbor Solicitations sent for DAD add
to the multicast scaling issues mentioned above.

It's worth underlining a couple of IPv6 features here:

1. Several subnet prefixes can be active on the same physical link.
   Therefore, a host may receive several different PIO messages and
   configure several routeable addresses per interface. Also, for
   example when using temporary addresses
   \[[RFC8981](https://www.rfc-editor.org/info/rfc8981)\], a host may
   have several simultaneous addresses *under the same prefix*. This is
   not an error; it's normal IPv6 behavior.

1. Both GUA and ULA addresses (see
   [2. Addresses](../02.%20IPv6%20Basic%20Technology/Addresses.md)) are
   routeable, even though the ULA is only routeable within an
   administrative boundary. Having both a GUA and a ULA simultaneously
   is also normal IPv6 behavior.

All IPv6 nodes **MUST** support SLAAC as described above, in case they
find themselves on a network where it is the only method of acquiring
addresses. However, some network operators prefer to manage addressing
using DHCPv6, as discussed in the next section. There is a global flag
for this in the RA message format known as the M bit (see
[RFC 4861](https://www.rfc-editor.org/info/rfc4861) for details). If
M=1, DHCPv6 is in use for address assignment. However, PIOs are still
needed to allow on-link determination, and link-local addresses are
still needed.

*More details*: This section and the previous one have summarized a
complex topic. Apart from the basic specifications
[RFC 4861](https://www.rfc-editor.org/info/rfc4861) and
[RFC 4862](https://www.rfc-editor.org/info/rfc4862), many other RFCs
exist on this topic, including for example:

- Enhanced Duplicate Address Detection,
  [RFC 7527](https://www.rfc-editor.org/info/rfc7527)

- IPv6 Subnet Model: The Relationship between Links and Subnet Prefixes,
  [RFC 5942](https://www.rfc-editor.org/info/rfc5942)

The numerous options allowed in RA messages, and the other ICMPv6
messages used for address resolution and SLAAC, are documented in IANA's
[IPv6 Neighbor Discovery Option Formats registry](https://www.iana.org/assignments/icmpv6-parameters/icmpv6-parameters.xhtml#icmpv6-parameters-5).

A simple network can operate with SLAAC as the only way to configure
host IPv6 connections. DNS parameters can be configured using RA options
(Recursive DNS Server Option and DNS Search List Option)
\[[RFC8106](https://www.rfc-editor.org/info/rfc8106)\].

However, as noted in the previous section, the dependency of neighbor
discovery and SLAAC on link-layer multicast does not scale well,
particularly on wireless networks. Also, the ability of SLAAC to assign
multiple addresses per host, especially dynamic temporary addresses
\[[RFC8981](https://www.rfc-editor.org/info/rfc8981)\], can create
scaling problems for routers.

When preferred by an operator, managed configuration, especially for
large networks, can be achieved using DHCPv6, as described in the next
section.

<!-- Link lines generated automatically; do not delete -->

### [<ins>Previous</ins>](Address%20resolution.md) [<ins>Next</ins>](Managed%20configuration.md) [<ins>Top</ins>](02.%20IPv6%20Basic%20Technology.md)
