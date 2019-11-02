#!/usr/local/bin/python
# coding: UTF-8

import getpass
import boto3
import json
import configparser

# Main function that runs the whole thing
def updateAll(profile_to_use):
    instances,groups = getEC2Instances(profile_to_use)
    # updateHosts(instances,groups)
    updateTerm(instances,groups,profile_to_use)

# Outputs to stdout the list of instances and returns EC2 instances as an array of dictionaries containing the following fields:
# name          => Instance name formed by the instance class/group and the domain prefix (aws.)
# group         => Group associated with the instance (webapp, vpn, etc.)
# index         => Index of this instance in the group

def getEC2Instances(profile_to_use):

    groups = {}
    instances = {}
    bastion=''
    vpc_bastion=''
    instance_bastion=''

    boto3.setup_default_session(profile_name=profile_to_use)

    client = boto3.client('ec2')

    def vpc_data(vpcid):
        vpc_bastion=''
        response_vpc = client.describe_vpcs(
            VpcIds=[
                vpcid,
            ]
        )
        # print(json.dumps(response_vpc, sort_keys=True, indent=4))
        for VPCs in response_vpc['Vpcs']:
            # if 'Tags' in response_vpc['Vpcs']:
            for tag in VPCs['Tags']:
                    if tag['Key'] == 'Bastion':
                            vpc_bastion = tag['Value']
                            break
        return vpc_bastion
    
    response = client.describe_instances(
            Filters = [{
                    'Name':'instance-state-name',
                    'Values': [
                            'running'
                    ]
                    }
            ]
    )


    

    
    for reservation in response['Reservations']:
            for instance in reservation['Instances']:      
                    for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                    name = tag['Value']
                                    break
                    for tag in instance['Tags']:
                            if tag['Key'] == 'Bastion':
                                    instance_bastion = tag['Value']
                                    break
                    ip = instance['NetworkInterfaces'][0]['PrivateIpAddress']
        
                    if name in groups:
                        groups[name] = groups[name] + 1
                    else:
                        groups[name] = 1


                    vpc_bastion = vpc_data(instance['VpcId'])
                    if vpc_bastion:
                        bastion = vpc_bastion
                    if instance_bastion:
                        bastion = instance_bastion

                    instances[ip] = {'name':'aws.' + profile_to_use + '.' + name,'index':groups[name],'group':name, 'bastion': bastion, 'vpc':reservation['Instances'][0]['VpcId']}
                    print(ip + "\t" + 'aws.' + profile_to_use + "." + name + "\t\t bastion: \"" + bastion + "\"")
   
    for ip in instances:
        instance = instances[ip]
        instance['name'] = instance['name'] + str(instance['index']) if groups[instance['group']] > 1 else instance['name']

    return instances, groups

# Updates the /etc/hosts file with the EC2 private addresses
# /etc/hosts must include the list of EC2 instances between two lines: the first contains '# AWS EC2' 
# and the last a single # character.
def updateHosts(instances,groups):
    handle = open('/etc/hosts')
    lines = handle.read().splitlines()    
    handle.close()
    state = False

    hout = open('/etc/hosts','wt')

    startDelimiter = "# AWS EC2"
    endDelimiter = "#"

    for line in lines:
        if line == startDelimiter:
            state = True
            continue
        if state == True and line == endDelimiter:
            state = False
            continue
        if not state:
            hout.write(line + "\n")

    hout.write(startDelimiter + "\n")
    for ip in instances:
        instance = instances[ip]
        name = instance['name']
        hout.write(ip + "\t" + name + "\n")
	
    hout.write(endDelimiter + "\n")
    hout.close()

def updateTerm(instances,groups,profile_to_use):
    handle = open('/Users/' + username + '/Library/Application Support/iTerm2/DynamicProfiles/aws-' + profile_to_use,'wt')
    state = False

    profiles = []

    for instance in instances:
        shortName = instances[instance]['name'][4:]
        group = instances[instance]['group']       
        tags =["Account: " + profile_to_use,"AWS",group] if groups[group] > 1 else ["Account: " + profile_to_use,'AWS']
        name = instances[instance]['name']

        if instances[instance]['bastion']:
            connection_command="ssh -J " + instances[instance]['bastion'] + " -oStrictHostKeyChecking=no -oUpdateHostKeys=yes " + instance
        else:
            connection_command="ssh -oStrictHostKeyChecking=no -oUpdateHostKeys=yes " + instance
            
        profile = {"Name":name,
                    "Guid":name,
                    "Badge Text":shortName,
                    "Tags":tags,
                    "Dynamic Profile Parent Name": "Bastión AWS",
                    "Custom Command" : "Yes",
                    "Initial Text" : connection_command
                    }

        profiles.append(profile)

    profiles = {"Profiles":(profiles)} 
    handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
    handle.close()


username = getpass.getuser()
config = configparser.ConfigParser()
config.read('/Users/' + username + '/.aws/credentials')
config.sections()
for i in reversed(config.sections()):
    print('working on profile: ' + i) 
    updateAll(i)
