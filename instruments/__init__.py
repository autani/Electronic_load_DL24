#!/usr/bin/python

import logging
import pyvisa as visa

from instruments import px100

log = logging.getLogger(__name__)


def resource_label(resource_name):
    head = resource_name.split('::')[0]
    if head.startswith('ASRL'):
        rest = head[4:]
        if rest.isdigit():
            return 'COM' + rest
        return rest
    return resource_name


class Instruments:
    def __init__(self):
        self.rm = visa.ResourceManager('@py')

    def list_serial_resources(self):
        try:
            resources = self.rm.list_resources('ASRL?*::INSTR')
        except Exception as err:
            log.debug('%s', err)
            return []
        return [r for r in resources if r.startswith('ASRL')]

    def open(self, resource_name):
        try:
            inst = self.rm.open_resource(resource_name)
        except Exception as err:
            log.debug('%s', err)
            log.debug("err opening instrument")
            return None

        try:
            driver = px100.PX100(inst)
            if driver.probe():
                log.debug("found " + driver.name)
                return driver
            log.debug("ko")
            inst.close()
            return None
        except Exception as err:
            log.debug('%s', type(err))
            log.debug('%s', err.args)
            log.debug('%s', err)
            log.debug("err")
            try:
                inst.close()
            except Exception as close_err:
                log.debug('%s', type(close_err))
                log.debug('%s', close_err.args)
                log.debug('%s', close_err)
                log.debug("no close")
            return None
