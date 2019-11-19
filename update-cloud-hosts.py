#!/usr/local/bin/python
# coding: UTF-8

import getpass
import boto3
import configparser
import json
import os
import yaml
import digitalocean
import shutil
import concurrent.futures


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
        iterm_tags = []
        bastion=get_tag_value(drop.tags, 'iTerm_bastion')
        drop_use_ip_public=get_tag_value(drop.tags, 'iTerm_use_ip_public')
        instance_use_bastion=get_tag_value(drop.tags, 'iTerm_use_bastion')
        or_host_name=get_tag_value(drop.tags, 'iTerm_host_name')
        # TODO: settingResolver, to support DO
        con_username = get_tag_value(drop.tags, 'iTerm_con_username')
        con_port = get_tag_value(drop.tags, 'iTerm_con_port')

        if or_host_name:
            drop_name = or_host_name
        else:
            drop_name = drop.name

        if script_config['DO'].get('use_ip_public', True) == True and ( drop_use_ip_public == 'True' or drop_use_ip_public == ''): # and 'PublicIpAddress' in instance:
            ip = drop.ip_address
        else:
            ip = drop.private_ip_address
            
        if drop.name in drop.tags:
            groups[drop.name] = groups[drop.name] + 1
        else:
            groups[drop.name] = 1

        dynamic_profile_parent_name = get_tag_value(drop.tags, 'iTerm_dynamic_profile_parent_name')
        if drop.tags:
            for tag in drop.tags:
                if tag:
                    iterm_tags.append(tag)
        
        iterm_tags += ip,drop.name,drop.size['slug']
        instances[ip] = {'name':instance_source + '.' + drop_name, 'group': drop_name,'index':groups[drop.name], 'dynamic_profile_parent_name': dynamic_profile_parent_name, 'iterm_tags': iterm_tags, 'InstanceType': drop.size['slug'], 'con_username': con_username, 'con_port': con_port, 'id': drop.id}
        print(profile['name'] + ": " + ip + "\t\t" + instance_source + '.' + drop_name + "\t\t associated bastion: \"" + bastion + "\"")
    
    updateTerm(instances,groups,instance_source)

def settingResolver(setting,instance,vpc_data_all,caller_type='AWS'):
    setting_value = ''
    setting_value = get_tag_value(instance.get('Tags', ''), setting)
    if not setting_value:
        setting_value = vpc_data(instance['VpcId'], setting, vpc_data_all)
        if not setting_value:
            setting = setting.rpartition('iTerm_')[2] # Strip iTerm prefix because settings are now read from conf files
            setting_value = profile.get(setting, '')
            if not setting_value:
                setting_value = script_config[caller_type].get(setting, '')
                if not setting_value:
                    setting_value = script_config["Local"].get(setting, '')
    return setting_value


def tagSplitter(flat_tags):
    for tag in flat_tags.split(','):
            if tag:
                return tag

def get_tag_value(tags, q_tag, sg=False):
    q_tag_value = ''
    for tag in tags:
        if q_tag == 'flat' and not sg:
            q_tag_value += tag['Key'] + ': ' + tag['Value'] + ","
        elif q_tag == 'flat' and sg == "sg":
            q_tag_value += tag['GroupName'] + ': ' + tag['GroupId'] + ","
        else:
            if tag['Key'] == q_tag:
                q_tag_value = tag['Value']
                break
    return q_tag_value


def vpc_data(vpcid, q_tag, response_vpc):
    q_tag_value = ''
    for vpc in response_vpc['Vpcs']:
        if vpc.get('Tags', False):
            if q_tag == "flat":
                for tag in vpc.get('Tags'):
                    if "iTerm" not in tag['Key']:
                        q_tag_value += "VPC." + tag['Key'] + ': ' + tag['Value'] + ","
            else:
                q_tag_value = get_tag_value(vpc.get('Tags'), q_tag)
    return q_tag_value


def fetchEC2Instance(instance, client, groups, instances, instance_source, reservation, vpc_data_all):
    con_port = ''
    instance_use_ip_public = ''
    instance_vpc_flat_tags = ''
    instance_flat_tags = ''
    iterm_tags = []

    instance_use_bastion = settingResolver('iTerm_con_username', instance, vpc_data_all)
    con_username = settingResolver('iTerm_con_username', instance, vpc_data_all)
    con_port = settingResolver('iTerm_con_port', instance, vpc_data_all)
    bastion = settingResolver('iTerm_bastion', instance, vpc_data_all)
    dynamic_profile_parent_name = settingResolver('iTerm_dynamic_profile_parent_name', instance, vpc_data_all)
    instance_flat_sgs = get_tag_value(instance['NetworkInterfaces'][0]['Groups'],'flat',"sg")
    instance_vpc_flat_tags = vpc_data(instance['VpcId'], "flat", vpc_data_all)
    
    if 'Tags' in instance:
        name = get_tag_value(instance['Tags'], 'Name')
        instance_flat_tags = get_tag_value(instance['Tags'], 'flat')
    else:
        name = instance['InstanceId']

    use_ip_public = settingResolver('iTerm_use_ip_public', instance, vpc_data_all)
    if use_ip_public == 'yes' and 'PublicIpAddress' in instance:
        ip = instance['PublicIpAddress']
    else:
        ip = instance['NetworkInterfaces'][0]['PrivateIpAddress']

    if name in groups:
        groups[name] = groups[name] + 1
    else:
        groups[name] = 1

    if 'PublicIpAddress' in instance:
        public_ip = instance['PublicIpAddress']
        iterm_tags.append(instance['PublicIpAddress'])
    else:
        public_ip = ''
    
    
    if instance_flat_tags:
        iterm_tags.append(tagSplitter(instance_flat_tags))
    if instance_vpc_flat_tags:
        iterm_tags.append(tagSplitter(instance_vpc_flat_tags))
    if instance_flat_sgs:
        iterm_tags.append(tagSplitter(instance_flat_sgs))

    iterm_tags.append(instance['VpcId'])
    iterm_tags.append(instance['InstanceId'])
    iterm_tags.append(instance['Placement']['AvailabilityZone'])
    iterm_tags.append(instance['InstanceType'])
    if instance['PublicDnsName']:
        iterm_tags.append(instance['PublicDnsName'])

    instances[ip] = {'name': instance_source + '.' + name, 'index': groups[name], 'group': name,
                     'bastion': bastion, 'vpc': reservation['Instances'][0]['VpcId'],
                     'instance_use_ip_public': instance_use_ip_public,
                     'instance_use_bastion': instance_use_bastion, 'ip_public': public_ip,
                     'dynamic_profile_parent_name': dynamic_profile_parent_name, 'iterm_tags': iterm_tags,
                     'InstanceType': instance['InstanceType'], 'con_username': con_username, 'con_port': con_port, 'id': instance['InstanceId']}
    return (ip + "\t" + instance['Placement']['AvailabilityZone'] + "\t" + instance_source + "." + name + "\t\t associated bastion: \"" + bastion + "\"")


def fetchEC2Region(region, profile_name, instances, groups, instance_source):
    if region in script_config['AWS']['exclude_regions']:
        print(profile_name + ": region " + "\"" + region + "\" is in excluded list")
        return

    client = boto3.client('ec2', region_name=region)

    if script_config['AWS']['skip_stopped'] == True:
        search_states = ['running']
    else:
        search_states = ['running', 'pending', 'shutting-down', 'terminated', 'stopping', 'stopped']

    response = client.describe_instances(
        Filters=[{
            'Name': 'instance-state-name',
            'Values': search_states
        }
        ]
    )

    vpc_data_all = client.describe_vpcs(
            VpcIds=[]
        )


    if response.get('Reservations',False):
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(fetchEC2Instance, instance, client, groups, instances, instance_source, reservation, vpc_data_all)
                    return_value = future.result()
                    print(profile_name + ": " + return_value)
    else:
        print(profile_name + ": \"" + region + "\" No instances found")

def getEC2Instances(profile):
    groups = {}
    instances = {}

    if isinstance(profile,dict):
        instance_source = "aws." + profile['name']
        profile_name = profile['name']
        boto3.setup_default_session(aws_access_key_id=profile['aws_access_key_id'],aws_secret_access_key=profile['aws_secret_access_key'],region_name="eu-central-1")
    else:
        instance_source = "aws." + profile
        boto3.setup_default_session(profile_name=profile,region_name="eu-central-1")
        profile_name = profile

    client = boto3.client('ec2')
    ec2_regions = [region['RegionName'] for region in client.describe_regions()['Regions']]


    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(fetchEC2Region, region , profile_name, instances, groups, instance_source) for region in ec2_regions]

    for ip in instances:
        instance = instances[ip]
        instance['name'] = instance['name'] + str(instance['index']) if groups[instance['group']] > 1 else instance['name']
    
    updateTerm(instances,groups,instance_source)


def updateTerm(instances,groups,instance_source):
    profiles = []

    for instance in instances:
        shortName = instances[instance]['name'][4:]
        group = instances[instance]['group']

        tags = ["Account: " + instance_source, instance]
        for tag in instances[instance]['iterm_tags']:
            tags.append(tag)
        if groups.get(group, 0) > 1:
            tags + groups


        if instances[instance].get('instance_use_ip_public', 'no') == "yes":
            ip_for_connection = instances[instance]['ip_public']
        else:
            ip_for_connection = instance
                
        connection_command = "ssh {}".format(ip_for_connection)

        if (instances[instance].get('bastion','') and instances[instance].get('instance_use_ip_public', 'no') != "yes") or instances[instance].get('instance_use_bastion', 'no') == "yes":
            connection_command="{} -J {}".format(connection_command,instances[instance]['bastion'])

        connection_command = "{} {}".format(connection_command, script_config["Local"]['ssh_base_string'])

        if instances[instance]['con_username']:
            connection_command = "{} -l {}".format(connection_command, instances[instance]['con_username'])
        
        if instances[instance]['con_port']:
            connection_command = "{} -p {}".format(connection_command, instances[instance]['con_port'])
        

        profile = {"Name":instances[instance]['name'],
                    "Guid":instances[instance]['id'],
                    "Badge Text":shortName + '\n' + instances[instance]['InstanceType'] + '\n' + ip_for_connection,
                    "Tags":tags,
                    "Dynamic Profile Parent Name": instances[instance].get('dynamic_profile_parent_name', ''),
                    "Custom Command" : "Yes",
                    "Initial Text" : connection_command
                    }

        profiles.append(profile)

    profiles = {"Profiles":(profiles)}
    handle = open(os.path.expanduser("~/Library/Application Support/iTerm2/DynamicProfiles/" + instance_source),'wt')
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
if __name__ == '__main__':
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
        shutil.copy2(os.path.join(script_dir,'config.yaml'), os.path.expanduser("~/.iTerm-cloud-profile-generator/"))


    for key in script_config_repo:
        script_config[key] = {**script_config_repo.get(key, {}),**script_config_user.get(key, {})}


    username = getpass.getuser()
    config = configparser.ConfigParser()

    # Static profiles iterator
    update_statics()


    # AWS profiles iterator
    if script_config['AWS'].get('profiles', False):
        for profile in script_config['AWS']['profiles']:
            print("Working on " + profile['name'])
            getEC2Instances(profile)
            
    # AWS profiles iterator from config file
    if script_config['AWS'].get('use_awscli_profiles', False):
        if os.path.exists(os.path.expanduser(script_config['AWS']['aws_credentials_file'])):
            config.read(os.path.expanduser(script_config['AWS']['aws_credentials_file']))
            for i in config.sections():
                if i not in script_config['AWS']['exclude_accounts']:
                    print('Working on AWS profile from credentials file: ' + i) 
                    getEC2Instances(i)
    
    # DO profiles iterator
    if script_config['DO'].get('profiles', False):
        for profile in script_config['DO']['profiles']:
            print("Working on " + profile['name'])
            getDOInstances(profile)
    
    print("\nWe wish you calm clouds and a serene path...\n")