#!/usr/bin/env python

#define db schema

from sqlalchemy import MetaData, create_engine
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import String, Integer, DateTime, Text

from os_dns_updater.utils.cfg import DNS_CONF

dbcred = DNS_CONF["db_user"]+":"+DNS_CONF["db_password"]
dbaddr = "mysql://"+dbcred+"@localhost/"+DNS_CONF["db_name"]
dbengine = create_engine(dbaddr)
dbmeta = MetaData()

#create empty db manually or fuel plugin

def init_tables():
    db_instance = Table("instance", dbmeta,
          Column("id", Integer, primary_key=True),
          Column("ip", String(20)),
          Column("name", String(90)),
          Column("uuid", String(40)),
          Column("state", String(90)),
          Column("dns_domain", String(90)),
          Column("created_at", DateTime),
          Column("updated_at", DateTime),
          Column("deleted_at", DateTime)
    )
    db_event = Table("event", dbmeta,
          #will be used for synchronization
          Column("id", Integer, primary_key=True),
          Column("fk_instance_id", Integer, ForeignKey("instance.id")),
          Column("type", String(24)),#enum
          Column("description", String(90)),
          Column("date", DateTime)
    )
    dbmeta.drop_all(dbengine)
    dbmeta.create_all(dbengine)

init_tables()
