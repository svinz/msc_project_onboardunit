import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime

def init_logging(name):
    # soure for global logger: https://stackoverflow.com/questions/7621897/python-logging-module-globally
    # add a streamhandler to show logs in terminal
    ch = logging.StreamHandler()
    # add a Filehandler to log to file
    t = datetime.now()
    filename = "logs/" + t.year.__str__() + t.month.__str__() + t.day.__str__() + t.hour.__str__() + t.minute.__str__() + t.second.__str__() + ".json"
    fh = logging.FileHandler(filename)
    # format the logs going to the terminal
    ch_formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    # setting the format for the terminal
    ch.setFormatter(ch_formatter)
    # setting the format for the logfile to a JSON format so it can be parsed almost directly to Elasticsearch
    # Using this tip to format the millisecond: https://stackoverflow.com/questions/6290739/python-logging-use-milliseconds-in-time-format/7517430#7517430
    file_formatter=logging.Formatter(
        "{ 'timestamp':'%(asctime)s.%(msecs)03dZ', 'name': '%(name)s', 'level': '%(levelname)s', 'message': '%(message)s'}",
        "%Y-%m-%dT%H:%M:%S"
    )
    file_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(module)s %(message)s')
    # Setting the formatter for the file handler
    fh.setFormatter(file_formatter)
    # create a logger
    LOG = logging.getLogger(name)
    LOG.setLevel(logging.DEBUG)
    LOG.addHandler(ch)
    LOG.addHandler(fh)
    return LOG

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

