#!/usr/bin/env python

# module to work with db

from sqlalchemy import MetaData, create_engine
from sqlalchemy import Column
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from os_dns_updater.utils.cfg import DNS_CONF
from os_dns_updater.utils.cfg import LOG_FILE

import re
import time
import datetime
import dateutil.relativedelta as timedelta
import hashlib
import logging as log

log_level = log.DEBUG if (DNS_CONF["debug"] == "True") else log.INFO
log.basicConfig(filename=LOG_FILE, level=log_level,
                format="%(levelname)s %(asctime)s %(message)s")

MAX_INST = int(DNS_CONF["maxcounter"]) # max number of instances of type in tenant
if not MAX_INST:
    MAX_INST = 4095
DBTTL = int(DNS_CONF["insttime"]) #time to store old data in db (state!=added)
if not DBTTL:
    DBTTL = 90

dbcred = DNS_CONF["db_user"]+":"+DNS_CONF["db_password"]
dbaddr = "mysql://"+dbcred+"@localhost/"+DNS_CONF["db_name"]
dbengine = create_engine(dbaddr, pool_recycle=120)
dbmeta = MetaData()
Base = declarative_base()

class Instance(Base):
    __tablename__ = "instance"
    id = Column(Integer, primary_key=True)
    ip = Column(String(20))
    name = Column(String(90))
    dns_domain = Column(String(90))
    uuid = Column(String(40))
    state = Column(String(40))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)

    def __init__(self, name, uuid, ip):
        self.ip = ip
        self.name = name
        self.uuid = uuid
        self.created_at = datetime.datetime.now()

#class Event(Base):
#    __tablename__ = "event"
#    id = Column(Integer, primary_key=True)
#    def __init__(self):
#        pass

Base.metadata.create_all(dbengine)

def check_and_clear():
    Session = scoped_session(sessionmaker(bind=dbengine))
    dbsession = Session()
    log.info("db check_and_clear started with options {} {}".format(MAX_INST,DBTTL))
    oldtime = datetime.datetime.today() - timedelta.relativedelta(days=DBTTL)
    log.info("looking for unregistered records older than {}".format(oldtime))
    inst = dbsession.query(Instance).filter(
                            Instance.state != 'added',
                            Instance.created_at <= oldtime
                            ).delete()
    try:
        dbsession.commit()
        log.info("{} records removed from db".format(len(inst)))
    except Exception as e:
        log.error(repr(e))
        dbsession.rollback()
    dbsession.bind.dispose()
    Session.remove()

def create_instance(iname, ip, uuid):
    Session = scoped_session(sessionmaker(bind=dbengine))
    dbsession = Session()
    inst = dbsession.query(Instance).filter(
                            Instance.name == iname,
                            Instance.state != 'added').first()
    if not inst:
        log.warning("instance {} was not found in db".format(iname))
        new_inst = Instance(iname, uuid, ip)
        dbsession.add(new_inst)
        new_inst.state = 'added'
        new_inst.dns_domain = DNS_CONF["domain"]
    else:
        inst.state = 'added'
        inst.dns_domain = DNS_CONF["domain"]
        inst.uuid = uuid
        inst.ip = ip
        inst.updated_at = datetime.datetime.now()
    try:
        dbsession.commit()
    except Exception as e:
        log.error(repr(e))
        dbsession.rollback()
    dbsession.bind.dispose()
    Session.remove()


def delete_instance(iname, uuid):
    Session = scoped_session(sessionmaker(bind=dbengine))
    dbsession = Session()
    inst = dbsession.query(Instance).filter(Instance.name == iname).first()
    if not inst:
        log.warning("instance {} was not found in db".format(iname))
    else:
        inst.state = 'deleted'
        inst.deleted_at = datetime.datetime.now()
        try:
            dbsession.commit()
        except Exception as e:
            log.error(repr(e))
            dbsession.rollback()
    dbsession.bind.dispose()
    Session.remove()

def generate_name(fqn, pname, dname):
    fqn = str(fqn)
    log.info("generating instance name for: {} {} {}".format(fqn,pname,dname))
    app = fqn.rsplit('.',1)[-1]
    app = app[:3]
    name = pname.split('-')[0]
    name = name[:9]
    pat = re.compile(r'^\D\d+')
    if pat.search(name) is None:
        name = 'None'
        log.warning("incorrect project name {}".format(pname))
    patt = "{}-{}-{}".format(DNS_CONF['region'],name,app)
    try:
        instnumber = num_from_patt(patt)
    except:
        instnumber = rstr(5)
    res = "{}-{}".format(patt,instnumber)
    return res

def num_from_patt(patt):
    patt1 = patt + '%'
    Session = scoped_session(sessionmaker(bind=dbengine))
    dbsession = Session()
    instances = dbsession.query(Instance).filter(
         Instance.name.like(patt1)).all()
    nums = []
    if not instances:
        log.debug("new instance of type {}".format(patt))
        res = 1
    else:
        res = 0
        for inst in instances:
            log.debug("found instance {}".format(inst.name))
            d = inst.name
            d = d.split('-')[3]
            d = int(d,16)
            nums.append(d)
    if not len(nums):
        res = 1
    else:
        rlist = list(set(range(1,MAX_INST)) - set(nums))
        res = rlist[0]
        log.debug("found new number: {}".format(res))
    res = str(hex(res))[2:]
    if len(res) == 1:
        res = '00'+res
    if len(res) == 2:
        res = '0'+res

    new_inst = Instance("{}-{}".format(patt,res), '', '')
    dbsession.add(new_inst)
    new_inst.state = 'reserved'
    new_inst.dns_domain = DNS_CONF["domain"]
    try:
        dbsession.commit()
    except Exception as e:
        dbsession.rollback()
    dbsession.bind.dispose()
    Session.remove()
    return res


def rstr(i):
    #random string of length i
    h = hashlib.sha1()
    h.update(str(time.time()*10000))
    rs = h.hexdigest()[:i]
    return rs

#unused right now:

def instance_exists(iname):
    Session = scoped_session(sessionmaker(bind=dbengine))
    dbsession = Session()
    inst = dbsession.query(Instance).filter(
         Instance.name==iname,
         Instance.state!='deleted',
         Instance.dns_domain==DNS_CONF['domain']).first()
    if not inst:
        log.debug("instance {} was not found in db".format(iname))
        res = False
    else:
        res = True
    dbsession.bind.dispose()
    Session.remove()
    return res

def update_instance():
    pass
