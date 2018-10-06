#!/usr/bin/python
# coding: UTF-8

import os
import re
import json

# Outputs to stdout the list of instances and returns EC2 instances as an array of dictionaries containing the following fields:
# name          => Instance name formed by the server class/group plus an index (i.e. webapp1, webapp2, etc.)
# serverClass   => Group associated with the instance (webapp, vpn, etc.)
def getEC2Instances():
    handle = os.popen('bash -e /usr/local/bin/aws_list')
    line = " "
    line = handle.read().splitlines()
    handle.close()
    servers = {}

    webapps = 1
    radius = 1

    for x in line:                

        parts = re.compile("(?:(?:[\w\-\.]+)\s*)(?:(?:[\w\-\.]+)\s*)(?:(?:[\w\-\.]+)\s*)(?:([\w\-\.]+)\s*)(?:(?:[\w\-\.]+)\s*)(?:([\w\-\.]+)\s*)")
        parts = parts.split(x)
        
        ip = parts[1]
        name = 'aws.' + parts[2]

        if ip == 'None':
            continue

        if name == 'aws.webapp':
            name += str(webapps)
            webapps += 1

        if name == 'aws.radius':
            name += str(radius)
            radius += 1

        print ip + "\t" + name
        servers[ip] = {'name':name,'serverClass':parts[2]}

    return servers

# Updates the /etc/hosts file with the EC2 private addresses
# /etc/hosts must include the list of EC2 instances between two lines: the first contains '# AWS EC2' 
# and the last a single # character.
def updateHosts(servers):
    handle = open('/etc/hosts')
    line = " "
    lines = handle.read().splitlines()
    handle.close()
    state = False

    hout = open('/etc/hosts','wt')

    startRe = re.compile("# AWS EC2")
    endRe = re.compile("#")

    for x in lines:
        if startRe.match(x):
            state = True
            continue
        if state == True and endRe.match(x):
            state = False
            continue
        if not state:
            hout.write(x + "\n")

    hout.write("# AWS EC2\n")
    for server in servers:        
        hout.write(server + "\t" + servers[server]['name'] + "\n")
	
    hout.write("#\n")
    hout.close()

def updateTerm(servers):
    handle = open('/Users/gmartin/Library/Application Support/iTerm2/DynamicProfiles/aws','wt')
    state = False

    profiles = []

    for server in servers:
        shortName = servers[server]['name'][4:]
        serverClass = servers[server]['serverClass']
        profile = {"Name":servers[server]['name'],
                    "Guid":servers[server]['name'],
                    "Badge Text":shortName,
                    "Tags":["AWS",serverClass],
                    "Dynamic Profile Parent Name": "Bastión AWS",
                    "Custom Command" : "Yes",
                    "Command" : "ssh -oStrictHostKeyChecking=no -oUpdateHostKeys=yes "+servers[server]['name']}
          
        profiles.append(profile)

    profiles = sorted(profiles, key=lambda x: x)
    
    profiles = {"Profiles":profiles} 
    handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
    handle.close()
    
servers = getEC2Instances()
updateHosts(servers)
updateTerm(servers)

