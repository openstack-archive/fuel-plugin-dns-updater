#!/usr/bin/env python

# module to work with rabbitmq (main)

#TODO!!! delete old records on time
from kombu import BrokerConnection
from kombu import Exchange
from kombu import Queue
from kombu.mixins import ConsumerMixin

from os_dns_updater.utils import dns_lib
from os_dns_updater.utils import db_lib
from os_dns_updater.utils.cfg import LOG_FILE, DNS_CONF

import json
import logging as log

log_level = log.DEBUG if (DNS_CONF["debug"] == "True") else log.INFO
log.basicConfig(filename=LOG_FILE, level=log_level,
                format="%(levelname)s %(name)s %(asctime)s %(message)s")

class DnsUpdater(ConsumerMixin):

    def __init__(self, connection):
        log.debug("service started with configuration:")
        log.debug(str(json.dumps(DNS_CONF,indent=4,separators=(",",":"))))
        log.debug("initialize rabbit")
        self.connection = connection
        return


    def get_consumers(self, consumer, channel):
        consumers = []
        exchanges = DNS_CONF["exchanges"]
        exchanges = exchanges.split(",")
        for exch in exchanges:
            exchange = Exchange(exch, type="topic", durable=False)
            queue = Queue(DNS_CONF["queue_name"], exchange,
                routing_key=DNS_CONF["routing_key"],
                durable=False, auto_delete=True, no_ack=True)
            consumers.append(consumer(queue, callbacks=[self.on_message]))
        return consumers

    def on_message(self, body, message):
        try:
            res = self._handle_message(body)
        except Exception as e:
            log.error(repr(e))


    def _handle_message(self, body):
        events = [DNS_CONF["event_create"],DNS_CONF["event_delete"]]
        v_key='oslo.message'
        if isinstance(body,dict):
            if v_key in body:
                log.debug("received message in v2 format")
                rdict=dict(body)
                jbody = rdict.get(v_key)
                if isinstance(jbody,str) or isinstance(jbody,unicode):
                    msgbody = json.loads(jbody)
                else:
                    msgbody = dict(jbody)
            else:
                log.debug("received message in v1 format")
                msgbody = dict(body)
            log.debug(str(json.dumps(msgbody,indent=4,separators=(",",":"))))
        else:
            log.warning("incorrect data type in oslo message: {}".format(type(body)))
            return False
        if ('event_type' in msgbody) and  ('payload' in msgbody):
            event_type = msgbody["event_type"]
            payload = msgbody["payload"]
        else:
            log.warning("unexpected message: {}".format(msgbody))
            return False
        if event_type in events:
            if "metadata" in payload:
                if "use_dns" in payload["metadata"]:
                    use_dns = (payload["metadata"]["use_dns"] == "yes")
                else:
                    log.debug("no dns metadata for event {}".format(event_type))
                    return False
            else:
                log.debug("No metadata for event {}".format(event_type))
                return False
        else:
            log.debug("event type ignored: {}".format(event_type))
            return False
        if use_dns:
            nova_hostname = payload["hostname"]
            nova_os_id = payload["instance_id"]
            if event_type == DNS_CONF["event_create"]:
                if not len(payload["fixed_ips"]):
                    log.warning("instance with no network")
                    return False
                #always use first interface (todo change this)
                nova_ip = payload["fixed_ips"][0]["address"]
                netname = payload["fixed_ips"][0]["label"]
                if netname not in DNS_CONF["networks"]:
                    log.warning("dns will not be used for {}".format(netname))
                    return False
                if "message" in payload:
                    if payload["message"] == "Success":
                        log.debug("Instance successfully created")
                    else:
                        log.warning("Error creating instance")
                        return False
                else:
                    log.warning("unknown instance state")
                lookup_addr = dns_lib.lookup_hostname(nova_hostname)
                if lookup_addr == nova_ip:
                    log.warning("Instance already has address : {}".format(nova_ip))
                    log.warning("Nothing to do for instance {}".format(nova_hostname))
                elif lookup_addr is not None:
                    log.error("Instance has different address: {}".format(lookup_addr))
                    log.error("Refused to add instance: {}".format(nova_hostname))
                    return False
                dns_lib.add_hostname(nova_hostname, nova_ip)
                assigned_addr = dns_lib.lookup_hostname(nova_hostname)
                if assigned_addr is None:
                    log.error("Dns server denied request for instance: {}".format(nova_hostname))
                    return False
                else:
                    log.info("Instance added to dns: {} {}".format(nova_hostname, assigned_addr))
                    #db_lib.create_instance(nova_hostname, nova_ip, nova_os_id)
            if event_type == DNS_CONF["event_delete"]:
                lookup_addr = dns_lib.lookup_hostname(nova_hostname)
                if lookup_addr is not None:
                    dns_lib.del_hostname(nova_hostname)
                    #db_lib.delete_instance(nova_hostname, nova_os_id)
                else:
                    log.warning("instance {} not found in dns".format(nova_hostname))
                    log.warning("nothing to do")
                    return False
            log.info("event of type {} processed".format(event_type))
            return True
        else:
            log.debug("Instance will not use dns for {}".format(event_type))
            return False

if __name__ == "__main__":
    amqp_hosts = DNS_CONF["amqp_hosts"].split(",")
    BROKER_LIST = []
    amqp_user = DNS_CONF["amqp_user"]
    amqp_password = DNS_CONF["amqp_password"]
    fs = DNS_CONF["failover_strategy"]
    for amqp_host in amqp_hosts:
        broker_uri = "amqp://{}:{}@{}//".format(amqp_user,amqp_password,amqp_host)
        BROKER_LIST.append(broker_uri)
    log.info("Connecting to broker {}".format(BROKER_LIST))
    with BrokerConnection(BROKER_LIST, failover_strategy=fs ) as connection:
        try:
            DnsUpdater(connection).run()
        except Exception, e:
            log.error(repr(e))

#TODO use oslo for config, log, db(?), messaging(?)
