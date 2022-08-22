# How to use this book

This book is, and we hope always will be, a work in progress. It is intended for people who
plan, deploy, maintain and operate computer networks using Internet Protocol version 6 (IPv6).
It is being written and updated by exactly such people. IPv6 is a mature protocol but every day
we gain more experience, products are updated, and quite often the underlying technical
standards are updated too. Therefore, this book will likewise be constantly updated. It's issued
under an [open source license](https://github.com/becarpenter/book6/blob/main/LICENSE.md). You are welcome to obtain a printed copy at cost price,but be aware that the book will evolve constantly.

The [list of contents](https://github.com/becarpenter/book6/blob/main/Contents.md)
should act as an on-line guide to the topics covered.
Most readers will probably not read from cover to cover. Design your own path through
the book. If you find errors, or missing topics, feel free to raise issues through
the book's [issue tracker](https://github.com/becarpenter/book6/issues).
Better still, become an [active contributor](https://github.com/becarpenter/book6/blob/main/CONTRIBUTING.md)
yourself; your contributions will be reviewed by an editorial team.

# How a user sees IPv6

The answer should be: *they don't*. In an ideal world, users would never
need to be aware of the lower layers of the protocol stack, and they certainly
should never have to see a hexadecimal number, or even be aware that they are using IPv6.
The goal of a network designer or operator should be to make this true.

However, it's unlikely that this will always succeed. It's likely that if a
user ever does see something specific to IPv6, it's probably at the worst possible
time: when there is a fault or a system configuration issue. That is exactly
when the user is either reading on-line help information, or in contact
with a help desk. It is therefore recommended to review any documentation
you provide to users or to help desk staff to make sure that when IPv6 is
mentioned, the information is complete, correct and up to date. It's also
important that configuration tools are designed to avoid or minimize any
need for users to enter IPv6 addresses by hand.

# How an application programmer sees IPv6

blah