#!/usr/bin/python
import DeviceAtlasCloud.Client
import json
import argparse

da = DeviceAtlasCloud.Client.Client()
parser = argparse.ArgumentParser(description='Device Atlas Cloud Probe')
parser.add_argument('-ua', action='store', type=str, help='User Agent string', dest='useragent')

args = parser.parse_args()

headers = {'user_agent': args.useragent}
data = da.getDeviceData(headers)

print json.JSONEncoder().encode(data)
