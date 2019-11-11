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


# Outputs to stdout the list of instances containing the following fields:
# name          => Instance name formed by the instance class/group and the domain prefix with appropriate cloud provider (aws., DO.,)
# group         => Group associated with the instance (webapp, vpn, etc.)
# index         => Index of this instance in the group

def getDOInstances(profile):
    instance_source = "DO." + profile['name']
    groups = {}
    instances = {}
        
    manager = digitalocean.Manager(token=profile['token'])
    my_droplets = manager.get_all_droplets()
    
    def get_tag_value(tags,q_tag):
            q_tag_value='' 
            tag_key=''
            tag_value=''
            for tag in tags:
                if ':' in tag and 'iTerm' in tag:
                    tag_key,tag_value = tag.split(':')
                    if tag_key == q_tag:
                        q_tag_value = tag_value.replace('_', ' ')
                        q_tag_value = tag_value.replace('-', '.')
                        break
            return q_tag_value
                       

    for drop in my_droplets:
        dynamic_profile_parent_name=''
        bastion=''
        vpc_bastion=''
        instance_bastion=''
        instance_use_ip_public=''
        instance_use_bastion=''
        public_ip=''

        bastion=get_tag_value(drop.tags, 'iTerm_bastion')
        drop_use_ip_public=get_tag_value(drop.tags, 'iTerm_use_ip_public')
        instance_use_bastion=get_tag_value(drop.tags, 'iTerm_use_bastion')

        if script_config['DO'].get('use_ip_public', True) == True and ( drop_use_ip_public == 'True' or drop_use_ip_public == ''): # and 'PublicIpAddress' in instance:
            ip = drop.ip_address
        else:
            ip = drop.private_ip_address
            
        if drop.name in drop.tags:
            groups[drop.name] = groups[drop.name] + 1
        else:
            groups[drop.name] = 1

        dynamic_profile_parent_name = get_tag_value(drop.tags, 'iTerm_dynamic_profile_parent_name')

        instances[ip] = {'name':instance_source + '.' + drop.name, 'group': drop.name,'index':groups[drop.name], 'dynamic_profile_parent_name': dynamic_profile_parent_name, 'public_ip': public_ip}
        print(ip + "\t\t" + instance_source + '.' + drop.name + "\t\t associated bastion: \"" + bastion + "\"")
    
    updateTerm(instances,groups,instance_source)



def getEC2Instances(profile):
    groups = {}
    instances = {}

    if isinstance(profile,dict):
    # if profile.get('aws_access_key_id', ""):
        instance_source = "aws." + profile['name']
        profile_name = profile['name']
        boto3.setup_default_session(aws_access_key_id=profile['aws_access_key_id'],aws_secret_access_key=profile['aws_secret_access_key'],region_name="eu-central-1")
    else:
        instance_source = "aws." + profile
        boto3.setup_default_session(profile_name=profile,region_name="eu-central-1")
        profile_name = profile
    
        
    
    
    client = boto3.client('ec2')
    ec2_regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    
    for region in ec2_regions:
        if region in script_config['AWS']['exclude_regions']:
            continue

        print("Working on AWS profile: " + profile_name + " region: " + region)
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
        
        if script_config['AWS']['skip_stopped'] == True:
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

                        if (vpc_use_ip_public == True or script_config['AWS']['use_ip_public'] == True) and 'PublicIpAddress' in instance:
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

                        instances[ip] = {'name':instance_source + '.' + name,'index':groups[name],'group':name, 'bastion': bastion, 'vpc':reservation['Instances'][0]['VpcId'], 'instance_use_ip_public': instance_use_ip_public, 'instance_use_bastion': instance_use_bastion, 'ip_public': public_ip, 'dynamic_profile_parent_name': dynamic_profile_parent_name}
                        # print(json.dumps(instances[ip], sort_keys=True, indent=4))
                        print(ip + "\t" + instance_source + "." + name + "\t\t associated bastion: \"" + bastion + "\"")
    
    for ip in instances:
        instance = instances[ip]
        instance['name'] = instance['name'] + str(instance['index']) if groups[instance['group']] > 1 else instance['name']
    
    updateTerm(instances,groups,instance_source)

def updateTerm(instances,groups,instance_source):
    handle = open(os.path.expanduser("~/Library/Application Support/iTerm2/DynamicProfiles/" + instance_source),'wt')
    state = False

    profiles = []

    for instance in instances:
        shortName = instances[instance]['name'][4:]
        group = instances[instance]['group']       
        tags =["Account: " + instance_source,group] if groups[group] > 1 else ["Account: " + instance_source]
        name = instances[instance]['name']

        if instances[instance].get('instance_use_ip_public', 'no') == "yes":
            ip_for_connection = instances[instance]['ip_public']
        else:
            ip_for_connection = instance
        

        if (instances[instance].get('bastion','') and instances[instance].get('instance_use_ip_public', 'no') != "yes") or instances[instance].get('instance_use_bastion', 'no') == "yes":
            connection_command="ssh "  + ip_for_connection + " -J " + instances[instance]['bastion'] + " -oStrictHostKeyChecking=no -oUpdateHostKeys=yes -oServerAliveInterval=30 -oAddKeysToAgent=no"
        else:
            connection_command="ssh "  + ip_for_connection + " -oStrictHostKeyChecking=no -oUpdateHostKeys=yes -oServerAliveInterval=30 -oAddKeysToAgent=no"
        profile = {"Name":name,
                    "Guid":name,
                    "Badge Text":shortName,
                    "Tags":tags,
                    "Dynamic Profile Parent Name": instances[instance].get('dynamic_profile_parent_name', ''),
                    "Custom Command" : "Yes",
                    "Initial Text" : connection_command
                    }

        profiles.append(profile)

    profiles = {"Profiles":(profiles)} 
    handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
    handle.close()

def update_statics():
    profiles =[]
    
    app_static_profile_handle = open(os.path.expanduser("~/Library/Application Support/iTerm2/DynamicProfiles/statics"),"wt")
    path_to_static_profiles = os.path.expanduser(script_config["Local"]['static_profiles'])
    
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
script_config = {}
script_config_user = {}
if os.path.isfile(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")):
    with open(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")) as conf_file:
        script_config_user = yaml.full_load(conf_file)
else:
    if not os.path.isdir(os.path.expanduser("~/.iTerm-cloud-profile-generator/")):
        os.makedirs(os.path.expanduser("~/.iTerm-cloud-profile-generator/"))
    shutil.copy2(os.path.join(script_dir,'config.yaml'), os.path.expanduser("~/.iTerm-cloud-profile-generator/")) # target filename is /dst/dir/file.ext


for key in script_config_repo:
    script_config[key] = {**script_config_repo.get(key, {}),**script_config_user.get(key, {})}


username = getpass.getuser()
config = configparser.ConfigParser()

# Static profiles iterator
update_statics()

# DO profiles iterator
profiles_to_use = {}
if script_config['DO'].get('profiles', False):
    for profile in script_config['DO']['profiles']:
        print("Working on " + profile['name'])
        getDOInstances(profile)        

# AWS profiles iterator
profiles_to_use = {}
if script_config['AWS'].get('profiles', False):
    for profile in script_config['AWS']['profiles']:
        print("Working on " + profile['name'])
        getEC2Instances(profile)
        
# AWS profiles iterator from config file
if os.path.exists(os.path.expanduser(script_config['AWS']['aws_credentials_file'])):
    config.read(os.path.expanduser(script_config['AWS']['aws_credentials_file']))
    for i in config.sections():
        if i not in script_config['AWS']['exclude_accounts']:
            print('Working on AWS profile from credentials file: ' + i) 
            getEC2Instances(i)
print("\nWe wish you calm clouds and a serene path...\n")