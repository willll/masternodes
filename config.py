"""
Globals !
"""
import logging
import json

file = open("config.json", "r")
config = json.load(file)

logging.basicConfig(
    filename="debug_rest_py.log",
    filemode="w",
    level=logging.INFO)
