#!/usr/bin/env python

from ConfigParser import SafeConfigParser

LOG_FILE = "/var/log/dns-updater.log"
CONF_PATH = "/etc/os_dns_updater/dns-updater.conf"

conflist = [
    "debug",
    "db_name",
    "db_user",
    "db_password",
    "exchanges",
    "queue_name",
    "routing_key",
    "event_create",
    "event_delete",
    "amqp_user",
    "amqp_password",
    "amqp_hosts",
    "failover_strategy",
    "domain",
    "networks",
    "region",
    "dns_keyfile",
    "nameserver",
    "ttl",
    "maxcounter",
    "insttime"
]

def _parse_config(confname, conflist):
    config = SafeConfigParser()
    try:
        config.read(confname)
    except Exception as e:
        pass
    cf =  {}
    for item in conflist:
        try:
            value = config.get("DEFAULT", item)
        except Exception as e:
            value = None
        cf[item] = value
    return cf

DNS_CONF = _parse_config(CONF_PATH,conflist)
#TODO use neutron port update events
