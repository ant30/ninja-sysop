#!/usr/bin/env python

import requests
import simplejson

api_url = 'http://localhost:6543/api/'
auth_url = 'http://localhost:6543/login/'
user = 'admin'
password = 'admin'

auth_response = requests.post(auth_url, dict(login=user, password=password))
cookies = auth_response.cookies

# get root info
response = requests.get(api_url, cookies=cookies)
groups = simplejson.loads(response.text)


for group in groups:
    print group
    response = requests.get(api_url + '%s/' % group, cookies=cookies)
    items = simplejson.loads(response.text)
    for item in items:
        itemv = item['item']
        if not item['protected']:
            print " --> %s, %s, %s" % (itemv['name'], itemv['type'], itemv['target'])
        else:
            print " x-> %s, %s, %s" % (itemv['name'], itemv['type'], itemv['target'])

