"""
Globals !
"""
import logging
import json
import memcached_config

file = open("config.json", "r")
config = json.load(file)

logging.basicConfig(
    filename="debug_rest_py.log",
    filemode="w",
    level=logging.INFO)

memcached = memcached_config.Memcached_config()
