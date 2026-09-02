#!/usr/bin/python

import pyvisa as visa

from instruments import px100


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
            print(err)
            return []
        return [r for r in resources if r.startswith('ASRL')]

    def open(self, resource_name):
        try:
            inst = self.rm.open_resource(resource_name)
        except Exception as err:
            print(err)
            print("err opening instrument")
            return None

        try:
            driver = px100.PX100(inst)
            if driver.probe():
                print("found " + driver.name)
                return driver
            print("ko")
            inst.close()
            return None
        except Exception as err:
            print(type(err))
            print(err.args)
            print(err)
            print("err")
            try:
                inst.close()
            except Exception as close_err:
                print(type(close_err))
                print(close_err.args)
                print(close_err)
                print("no close")
            return None
