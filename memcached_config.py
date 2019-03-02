from pymemcache.client import base
import json
import subprocess
import psutil

def json_serializer(key, value):
    if type(value) == str:
        return value, 1
    return json.dumps(value), 2

def json_deserializer(key, value, flags):
   if flags == 1:
       return value
   if flags == 2:
       return json.loads(value)
   raise Exception("Unknown serialization format")


class Memcached_config(object):
    def __init__(self):
        # start memcached
        if not "memcached" in (p.name() for p in psutil.process_iter()):
            subprocess.Popen(["memcached"])

        # http://code.activestate.com/recipes/578011-json-instead-of-pickle-for-memcached/
        self.client = base.Client(server=('127.0.0.1',11211),
                                  serializer=json_serializer,
                                  deserializer=json_deserializer)
