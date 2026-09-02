from datetime import datetime
from os import path
import logging

from pandas import DataFrame, concat

log = logging.getLogger(__name__)


class DataStore:
    def __init__(self):
        self.reset()

    def __bool__(self):
        return len(self.lastrow) > 0

    def reset(self):
        self.lastrow = {}
        self.data = DataFrame()

    def append(self, row):
        log.debug('%s', row)
        self.lastrow = row
        self.data = concat([self.data, DataFrame([row])], ignore_index=True)

    def write(self, basedir, prefix):
        filename = "{}_raw_{}.csv".format(prefix, datetime.now().strftime("%Y%m%d_%H%M%S"))
        full_path = path.join(basedir, filename)
        export_rows = self.data.drop_duplicates()
        if export_rows.shape[0]:
            log.debug("Write RAW data to {}".format(path.relpath(full_path)))
            self.data.drop_duplicates().to_csv(full_path)
        else:
            log.debug("no data")

    def plot(self, **args):
        return self.data.plot(**args)

    def lastval(self, key):
        return self.lastrow[key]

    def setlastval(self, key, val):
        self.lastrow[key] = val
