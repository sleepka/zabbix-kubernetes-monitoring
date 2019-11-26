#!/usr/bin/env python

# Zabbix Kubernetes monitoring
# https://github.com/sleepka/zabbix-kubernetes-monitoring
# by Viktor Kravchenko (cryptox@cryptox.net)

import subprocess
import sys
import os
import json
import time

os.environ["KUBECONFIG"] = "/var/lib/zabbix/.kube/config"

kubectl='/usr/bin/kubectl' if os.path.isfile('/usr/bin/kubectl') else '/usr/local/bin/kubectl'

result = {'data':[]}

targets = ['pods','nodes','containers','deployments','apiservices','componentstatuses']
target = 'pods' if sys.argv[2] == 'containers' else sys.argv[2]

def rawdata(qtime=30):
    if sys.argv[2] in targets:
        tmp_file='/tmp/zbx-'+target+'.tmp'
        tmp_file_exists=True if os.path.isfile(tmp_file) else False
        if os.path.isfile(tmp_file) and (time.time()-os.path.getmtime(tmp_file)) <= qtime:
            file = open(tmp_file,'r')
            rawdata=file.read()
            file.close()
        else:
            rawdata = subprocess.check_output(kubectl + ' get ' + sys.argv[2] +' -A -o json',shell=True)
            file = open(tmp_file,'w')
            file.write(rawdata)
            file.close()
            #os.chmod(tmp_file, 0o666) if !tmp_file_exists
        return rawdata
    else:
        return false

if sys.argv[2] in targets:

	if 'discovery' in sys.argv[1]:
	    # discovery
            data = json.loads(rawdata())
            for item in data['items']:            
                if 'nodes' == sys.argv[2] or 'componentstatuses' == sys.argv[2] or 'apiservices' == sys.argv[2]:
		    result['data'].append({'{#NAME}':item['metadata']['name']})
	        elif 'containers' == sys.argv[2]:
		    for cont in item['spec']['containers']:
		        result['data'].append({'{#NAME}':item['metadata']['name'],'{#NAMESPACE}':item['metadata']['namespace'],'{#CONTAINER}':cont['name']})
		else:
		    result['data'].append({'{#NAME}':item['metadata']['name'],'{#NAMESPACE}':item['metadata']['namespace']})
            print json.dumps(result)

	elif 'stats' in sys.argv[1]:
	    # stats
            data = json.loads(rawdata(100))
            if 'pods' == sys.argv[2] or 'deployments' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['namespace'] == sys.argv[3] and item['metadata']['name'] == sys.argv[4]:
                        if 'statusPhase' == sys.argv[5]:
                            print item['status']['phase']
                        elif 'statusReason' == sys.argv[5]:
                            print item['status']['reason'] if 'reason' in item['status'] else 'none'
                        elif 'statusReady' == sys.argv[5]:
                            for status in item['status']['conditions']:
                                if status['type'] == 'Ready' or (status['type'] == 'Available' and 'deployments' == sys.argv[2]):
                                    print status['status']
                                    break
                        elif 'containerReady' == sys.argv[5]:
                            for status in item['status']['containerStatuses']:
                                if status['name'] == sys.argv[6]:
                                    print status['ready']
                                    break
                        elif 'containerRestarts' == sys.argv[5]:
                            for status in item['status']['containerStatuses']:
                                if status['name'] == sys.argv[6]:
                                    print status['restartCount']
                                    break
                        elif 'Replicas' == sys.argv[5]:
                            print item['spec']['replicas']
                        elif 'updatedReplicas' == sys.argv[5]:
                            print item['status']['updatedReplicas']
                        break
            if 'nodes' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['name'] == sys.argv[3]:
                        for status in item['status']['conditions']:
                            if status['type'] == sys.argv[4]:
                                print status['status']
                                break
            if 'componentstatuses' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['name'] == sys.argv[3]:
                        for status in item['conditions']:
                            if status['type'] == sys.argv[4]:
                                print status['status']
                                break
            if 'apiservices' == sys.argv[2]:
                for item in data['items']:
                    if item['metadata']['name'] == sys.argv[3]:
                        for status in item['status']['conditions']:
                            if status['type'] == sys.argv[4]:
                                print status['status']
                                break
else:
	result['data'].append({'Error':'No such target '+sys.argv[2]})

