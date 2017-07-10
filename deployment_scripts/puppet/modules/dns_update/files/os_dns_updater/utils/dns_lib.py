#!/usr/bin/env python

# module to work with dns

import dns.resolver
import dns.reversename
import dns.query
import dns.zone
import dns.exception
import dns.name
from subprocess import Popen, PIPE
import logging as log

from os_dns_updater.utils.cfg import LOG_FILE
from os_dns_updater.utils.cfg import DNS_CONF

log_level = log.DEBUG if (DNS_CONF["debug"] == "True") else log.INFO
log.basicConfig(filename=LOG_FILE, level=log_level,
                format="%(levelname)s %(asctime)s %(message)s")


NSUPDATE_ADD = "\
server {nameserver}\n\
update add {hostname} {ttl} A {hostaddr}\n\
send"

NSUPDATE_DEL = "\
server {nameserver}\n\
update delete {hostname} A\n\
send"

def dns_zone_to_text(dnsconf=DNS_CONF):
    z = dns.zone.from_xfr(dns.query.xfr(dnsconf["nameserver"],dnsconf["domain"]))
    names = z.nodes.keys()
    names.sort()
    res = []
    for n in names:
        res.append(z[n].to_text(n))
    log.info("dns zone loaded{}".format(res))
    return res

def lookup_hostname(name,dnsconf=DNS_CONF):
    try:
        resolv = dns.resolver.Resolver(configure=False)
        log.debug("initialize resolver")
        resolv.nameservers.append(dnsconf["nameserver"])
        resolv.domain = dns.name.from_text(dnsconf["domain"])
        resolv.search.append(dns.name.from_text(dnsconf["domain"]))
        log.debug("resolver {} {}".format(dnsconf["nameserver"],dnsconf["domain"]))
        try:
            answer = resolv.query(name)
            addr = answer.rrset[0]
            log.info("lookup host {} at {}".format(name, addr))
        except dns.exception.DNSException as e:#handle nxdomain - not an error
            log.info("instance not found: {}".format(repr(e)))
            addr = None
    except dns.exception.DNSException as e:
        log.error(repr(e))
        addr = None
    return addr

def dns_update(hostname, script, hostaddr=""):
        hostname = hostname + "." + DNS_CONF["domain"]
        p = Popen(["/usr/bin/nsupdate", "-k", DNS_CONF["dns_keyfile"]], stdin=PIPE)
        inp = script.format(
            nameserver=DNS_CONF["nameserver"],
            hostname=hostname, ttl=DNS_CONF["ttl"], hostaddr=hostaddr)
        p.communicate(input=inp)

def add_hostname(name, ip):
    log.info("adding to dns {} {}".format(name, ip))
    dns_update(name, NSUPDATE_ADD, ip)

def del_hostname(name):
    log.info("deleting from dns {}".format(name))
    dns_update(name, NSUPDATE_DEL)

#TODO always use dnspython do not use subprocess
