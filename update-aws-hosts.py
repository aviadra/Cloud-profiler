#!/usr/local/bin/python
# coding: UTF-8

import getpass
import boto3
import json
import configparser
import json
import os
import sys
import yaml
import digitalocean
import shutil

# Main function that runs the whole thing
def updateAll(profile_to_use):
    instances,groups = getEC2Instances(profile_to_use)
    # updateHosts(instances,groups)
    updateTerm(instances,groups,profile_to_use)

# Outputs to stdout the list of instances and returns EC2 instances as an array of dictionaries containing the following fields:
# name          => Instance name formed by the instance class/group and the domain prefix (aws.)
# group         => Group associated with the instance (webapp, vpn, etc.)
# index         => Index of this instance in the group

def getDOInstances():
    groups = {}
    instances = {}
        
    manager = digitalocean.Manager()
    my_droplets = manager.get_all_droplets()
    print(my_droplets)



def getEC2Instances(profile_to_use):

    groups = {}
    instances = {}

    boto3.setup_default_session(profile_name=profile_to_use)
    client = boto3.client('ec2')
    ec2_regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    
    for region in ec2_regions:
        if region in script_config['exclude_regions']:
            continue

        print("Working on AWS profile: " + profile_to_use + " region: " + region)
        client = boto3.client('ec2',region_name=region)
        
        def get_tag_value(tags,q_tag):
            q_tag_value='' 
            for tag in tags:
                if tag['Key'] == q_tag:
                        q_tag_value = tag['Value']
                        break
            return q_tag_value
        
        def vpc_data(vpcid,q_tag):
            q_tag_value=''
            response_vpc = client.describe_vpcs(
                VpcIds=[
                    vpcid,
                ]
            )
            if 'Tags' in response_vpc['Vpcs'][0]:
                q_tag_value=get_tag_value(response_vpc['Vpcs'][0]['Tags'], q_tag)
            return q_tag_value
        
        if script_config['skip_stopped'] == True:
            search_states = ['running']
        else:
            search_states = ['running','pending','shutting-down', 'terminated', 'stopping', 'stopped']
        
        response = client.describe_instances(
                Filters = [{
                        'Name':'instance-state-name',
                        'Values': search_states
                        }
                ]
        )

        for reservation in response['Reservations']:
                instance_dynamic_profile_parent_name=''
                dynamic_profile_parent_name=''
                bastion=''
                vpc_bastion=''
                instance_bastion=''
                instance_use_ip_public=''
                instance_use_bastion=''
                public_ip=''
                for instance in reservation['Instances']:      
                        if 'Tags' in instance:
                            name=get_tag_value(instance['Tags'], 'Name')
                            instance_bastion=get_tag_value(instance['Tags'], 'iTerm_bastion')
                            instance_use_ip_public=get_tag_value(instance['Tags'], 'iTerm_use_ip_public')
                            instance_use_bastion=get_tag_value(instance['Tags'], 'iTerm_use_bastion')
                            instance_dynamic_profile_parent_name=get_tag_value(instance['Tags'], 'iTerm_dynamic_profile_parent_name')
                        else:
                            name=instance['InstanceId']

                        vpc_use_ip_public = vpc_data(instance['VpcId'], 'iTerm_use_ip_public')

                        if (vpc_use_ip_public == True or script_config['use_ip_public'] == True) and 'PublicIpAddress' in instance:
                            ip = instance['PublicIpAddress']
                        else:
                            ip = instance['NetworkInterfaces'][0]['PrivateIpAddress']
            
                        if name in groups:
                            groups[name] = groups[name] + 1
                        else:
                            groups[name] = 1

                        vpc_bastion = vpc_data(instance['VpcId'], 'iTerm_bastion')
                        if vpc_bastion:
                            bastion = vpc_bastion
                        if instance_bastion:
                            bastion = instance_bastion

                        vpc_dynamic_profile_parent_name = vpc_data(instance['VpcId'], 'iTerm_dynamic_profile_parent_name')
                        if vpc_dynamic_profile_parent_name:
                            dynamic_profile_parent_name = vpc_dynamic_profile_parent_name
                        if instance_dynamic_profile_parent_name:
                            dynamic_profile_parent_name = instance_dynamic_profile_parent_name

                        if 'PublicIpAddress' in instance:
                            public_ip=instance['PublicIpAddress']
                        else:
                            public_ip=''

                        instances[ip] = {'name':'aws.' + profile_to_use + '.' + name,'index':groups[name],'group':name, 'bastion': bastion, 'vpc':reservation['Instances'][0]['VpcId'], 'instance_use_ip_public': instance_use_ip_public, 'instance_use_bastion': instance_use_bastion, 'ip_public': public_ip, 'dynamic_profile_parent_name': dynamic_profile_parent_name}
                        # print(json.dumps(instances[ip], sort_keys=True, indent=4))
                        print(ip + "\t" + 'aws.' + profile_to_use + "." + name + "\t\t associated bastion: \"" + bastion + "\"")
    
    for ip in instances:
        instance = instances[ip]
        instance['name'] = instance['name'] + str(instance['index']) if groups[instance['group']] > 1 else instance['name']

    return instances, groups

def updateTerm(instances,groups,profile_to_use):
    handle = open('/Users/' + username + '/Library/Application Support/iTerm2/DynamicProfiles/aws-' + profile_to_use,'wt')
    state = False

    profiles = []

    for instance in instances:
        shortName = instances[instance]['name'][4:]
        group = instances[instance]['group']       
        tags =["Account: " + profile_to_use,"AWS",group] if groups[group] > 1 else ["Account: " + profile_to_use,'AWS']
        name = instances[instance]['name']

        if instances[instance]['instance_use_ip_public'] == "yes":
            ip_for_connection = instances[instance]['ip_public']
        else:
            ip_for_connection = instance
        

        if (instances[instance]['bastion'] and instances[instance]['instance_use_ip_public'] != "yes") or instances[instance]['instance_use_bastion'] == "yes":
            connection_command="ssh "  + ip_for_connection + " -J " + instances[instance]['bastion'] + " -oStrictHostKeyChecking=no -oUpdateHostKeys=yes -oServerAliveInterval=30 -oAddKeysToAgent=no"
        else:
            connection_command="ssh "  + ip_for_connection + " -oStrictHostKeyChecking=no -oUpdateHostKeys=yes -oServerAliveInterval=30 -oAddKeysToAgent=no"
        profile = {"Name":name,
                    "Guid":name,
                    "Badge Text":shortName,
                    "Tags":tags,
                    "Dynamic Profile Parent Name": instances[instance]['dynamic_profile_parent_name'],
                    "Custom Command" : "Yes",
                    "Initial Text" : connection_command
                    }

        profiles.append(profile)

    profiles = {"Profiles":(profiles)} 
    handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
    handle.close()

def update_statics():
    profiles =[]
    
    app_static_profile_handle = open('/Users/' + username + '/Library/Application Support/iTerm2/DynamicProfiles/statics','wt')
    path_to_static_profiles = os.path.expanduser(script_config['static_profiles'])
    
    for root, dirs, files in os.walk(path_to_static_profiles, topdown=False):
        for name in files:
            if name == '.DS_Store':
                print("Static profiles, skipping \".DS_Store\"")
                continue
            print("Working on static profile: "+ name)
            static_profile_handle=open(os.path.join(root, name))
            profiles.append(json.load(static_profile_handle))

    
    profiles = {"Profiles":(profiles)} 
    app_static_profile_handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
    app_static_profile_handle.close()



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


#MAIN
script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))


# From repo
with open(os.path.join(script_dir,'config.yaml')) as conf_file:
    script_config_repo = yaml.full_load(conf_file)

# From user home direcotry
script_config_user = {}
if os.path.isfile(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")):
    with open(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")) as conf_file:
        script_config_user = yaml.full_load(conf_file)
else:
    os.makedirs(os.path.expanduser("~/.iTerm-cloud-profile-generator/"))
    shutil.copy2(os.path.join(script_dir,'config.yaml'), os.path.expanduser("~/.iTerm-cloud-profile-generator/")) # target filename is /dst/dir/file.ext


script_config = {**script_config_repo['AWS'],**script_config_user.get('AWS', {})}


username = getpass.getuser()
config = configparser.ConfigParser()

config.read(os.path.expanduser(script_config['aws_credentials_file']))
update_statics()
for i in config.sections():
    if i not in script_config['exclude_accounts']:
        print('Working on AWS profile: ' + i) 
        updateAll(i)
print("\nWe wish you calm clouds and a serene path...\n")