#!/usr/bin/env python
# module to clear db every hour_of_day
import time, datetime
from os_dns_updater.utils import db_lib
from os_dns_updater.utils.cfg import DNS_CONF
from os_dns_updater.utils.cfg import LOG_FILE

import logging as log

log_level = log.DEBUG if (DNS_CONF["debug"] == "True") else log.INFO
log.basicConfig(filename=LOG_FILE, level=log_level,
                format="%(levelname)s %(asctime)s %(message)s")

while 1:
    hour_of_day = datetime.datetime.timetuple(datetime.datetime.now())[3]
    if hour_of_day == 21:
        db_lib.check_and_clear()
    time.sleep(3599)
