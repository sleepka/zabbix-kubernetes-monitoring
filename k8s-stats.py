#!/usr/bin/env python

import subprocess
import sys
import os
import json
import time
#Needs for azure-fix to ignore selfsigned ssl cert 
import ssl

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

api_server = 'https://API_SERVER_URL'
token = 'TOKEN'

targets = ['pods','nodes','containers','deployments','apiservices','componentstatuses']
target = 'pods' if 'containers' == sys.argv[2] else sys.argv[2]

if 'pods' == target or 'nodes' == target or 'componentstatuses' == target:
    api_req = '/api/v1/'+target
elif 'deployments' == target:
    api_req = '/apis/apps/v1/'+target
elif 'apiservices' == target:
    api_req = '/apis/apiregistration.k8s.io/v1/'+target

def rawdata(qtime=30):
    if sys.argv[2] in targets:
        tmp_file='/tmp/zbx-'+target+'.tmp'
        tmp_file_exists=True if os.path.isfile(tmp_file) else False
        if tmp_file_exists and (time.time()-os.path.getmtime(tmp_file)) <= qtime:
            file = open(tmp_file,'r')
            rawdata=file.read()
            file.close()
        else:
            #azure-fix to ignore selfsigned ssl cert
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib2.Request(api_server + api_req)
            req.add_header('Authorization', 'Bearer ' + token)
            #Use context with no ssl check for selfsigned certs
            rawdata = urllib2.urlopen(req, context=ctx).read()

            file = open(tmp_file,'wb')
            file.write(rawdata)
            file.close()
            if not tmp_file_exists:
                os.chmod(tmp_file, 0o666)
        return rawdata
    else:
        return false


if sys.argv[2] in targets:

        if 'discovery' == sys.argv[1]:

            # discovery

            result = {'data':[]}
            data = json.loads(rawdata())

            for item in data['items']:            
                if 'nodes' == sys.argv[2] or 'componentstatuses' == sys.argv[2] or 'apiservices' == sys.argv[2]:
                    result['data'].append({'{#NAME}':item['metadata']['name']})
                elif 'containers' == sys.argv[2]:
                    for cont in item['spec']['containers']:
                        result['data'].append({'{#NAME}':item['metadata']['name'],'{#NAMESPACE}':item['metadata']['namespace'],'{#CONTAINER}':cont['name']})
                else:
                    result['data'].append({'{#NAME}':item['metadata']['name'],'{#NAMESPACE}':item['metadata']['namespace']})

            print(json.dumps(result))

        elif 'stats' == sys.argv[1]:

            # stats

            data = json.loads(rawdata(100))

            if 'pods' == sys.argv[2] or 'deployments' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['namespace'] == sys.argv[3] and item['metadata']['name'] == sys.argv[4]:
                        if 'statusPhase' == sys.argv[5]:
                            print(item['status']['phase'])
                        elif 'statusReason' == sys.argv[5]:
                            if 'reason' in item['status']:
                                print (item['status']['reason'])
                        elif 'statusReady' == sys.argv[5]:
                            for status in item['status']['conditions']:
                                if status['type'] == 'Ready' or (status['type'] == 'Available' and 'deployments' == sys.argv[2]):
                                    print(status['status'])
                                    break
                        elif 'containerReady' == sys.argv[5]:
                            for status in item['status']['containerStatuses']:
                                if status['name'] == sys.argv[6]:
                                    for state in status['state']:
                                        if state == 'terminated':
                                            if status['state']['terminated']['reason'] == 'Completed':
                                                print('True')
                                                break
                                    else:
                                        print(status['ready'])
                                        break
                        elif 'containerRestarts' == sys.argv[5]:
                            for status in item['status']['containerStatuses']:
                                if status['name'] == sys.argv[6]:
                                    print(status['restartCount'])
                                    break
                        elif 'Replicas' == sys.argv[5]:
                            print (item['spec']['replicas'])
                        elif 'updatedReplicas' == sys.argv[5]:
                            print (item['status']['updatedReplicas'])
                        break
            if 'nodes' == sys.argv[2] or 'apiservices' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['name'] == sys.argv[3]:
                        for status in item['status']['conditions']:
                            if status['type'] == sys.argv[4]:
                                print(status['status'])
                                break
            elif 'componentstatuses' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['name'] == sys.argv[3]:
                        for status in item['conditions']:
                            if status['type'] == sys.argv[4]:
                                print(status['status'])
                                break
