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
import base64
from inputimeout import inputimeout, TimeoutOccurred
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from pathlib import Path
import platform


# Outputs to stdout the list of instances containing the following fields:
# name          => Instance name formed by the instance class/group and the domain prefix with appropriate cloud provider (aws., DO.,)
# group         => Group associated with the instance (webapp, vpn, etc.)
# index         => Index of this instance in the group

def BadgeMe(instance_key,instance):
    end_badge = []
    Name = instance['Name'].split('.')
    if len(Name) == 4:
        Name_formatted = f"""Instance name: {Name[3]}
                            Cloud provIdor: {Name[0]}
                            Cloud account: {Name[2]}
                            Account profile: {Name[1]}"""
    else:
        Name_formatted = f"""Instance name: {Name[2]}
                            Cloud provIdor: {Name[0]}
                            Account profile: {Name[1]}"""
    all_badge_toggeles = script_config["Local"].get("Badge_info_to_display", False)
    if all_badge_toggeles == False:
        value_to_return = f"""  {Name_formatted}
                                InstanceType: {instance['InstanceType']}
                                Ip_public: {instance['Ip_public']}
                                Main_IP: {instance_key}
                            """
    else:
        for badge,toggle in all_badge_toggeles.items():
            if toggle or isinstance(toggle,list):
                if badge == "Instance_key":
                    end_badge.append(f"Main_IP: {instance_key}")
                if badge == "Name" and toggle == "Formatted":
                    end_badge.append(f"{Name_formatted}")
                    continue
                if badge and instance['Password'][1] != "":
                    end_badge.append(f"{badge}: {instance['Password'][1]}")
                if instance.get(badge, False) and badge != "Password":
                    end_badge.append(f"{badge}: {str(instance[badge])}")
                if isinstance(toggle,list) and len(toggle) != 0:
                    end_badge.append(q_tag_flat(instance['Iterm_tags'], toggle))
                if isinstance(toggle,list) and len(toggle) == 0:
                    end_badge.append(f"{instance['Iterm_tags']}")
        value_to_return = '\n'.join(filter(lambda x: x != "", end_badge))
    return value_to_return


def q_tag_flat(tags,badge_tag_to_display):
    return_value = []
    for tag in tags:
        if tag.split(':')[0] in badge_tag_to_display:
            return_value.append(tag)
    return_value_fromatted = f"iTerm tags: {', '.join(filter(lambda x: x != '', return_value))}"
    return return_value_fromatted

def decrypt(ciphertext, keyfile):
    if not os.path.isfile(os.path.expanduser(keyfile)):
        return [False, f"Decryption key not found at {keyfile}."]
    input = open(os.path.expanduser(keyfile))
    key = RSA.importKey(input.read())
    input.close()
    cipher = PKCS1_v1_5.new(key)
    plaintext = cipher.decrypt(ciphertext, None).decode('utf-8')
    return [True, plaintext]

def settingResolver(setting,instance,vpc_data_all,caller_type='AWS', setting_value = False):
    if caller_type == 'AWS':
        setting_value = get_tag_value(instance.get('Tags', ''), setting, False, setting_value)
    if caller_type == 'DO':
        setting_value = get_DO_tag_value(instance.tags, setting, setting_value)
    if setting_value == False:
        if caller_type == 'AWS' and instance['State']['Name'] != "terminated":
            setting_value = vpc_data(instance['VpcId'], setting, vpc_data_all)
        if caller_type == 'DO':
            pass
        if setting_value == False:
            if 'iTerm_' in setting:
                setting = setting.rpartition('iTerm_')[2] # Strip iTerm prefix because settings are now read from conf files
            if 'Cloud_Profiler_' in setting:
                setting = setting.rpartition('Cloud_Profiler_')[2] # Strip iTerm prefix because settings are now read from conf files
            setting_value = profile.get(setting, False)
            if setting_value == False:
                setting_value = script_config[caller_type].get(setting, False)
                if setting_value == False:
                    setting_value = script_config["Local"].get(setting, False)
    return setting_value

def get_DO_tag_value(tags,q_tag, q_tag_value):
            tag_key=''
            tag_value=''
            for tag in tags:
                if ':' in tag and ('iTerm' in tag or 'Cloud_Profiler' in tags):
                    tag_key,tag_value = tag.split(':')
                    if tag_key == q_tag.casefold():
                        q_tag_value = tag_value.replace('_', ' ')
                        q_tag_value = tag_value.replace('-', '.')
                        break
            return q_tag_value
            
def get_tag_value(tags, q_tag, sg=False, q_tag_value = False):
    for tag in tags:
        if 'iTerm_' in tag.get('Key', ''):
            tag['Key'] = tag['Key'].rpartition('iTerm_')[2]
        if 'Cloud_Profiler_' in tag.get('Key', ''):
            tag['Key'] = tag['Key'].rpartition('Cloud_Profiler_')[2]
        if q_tag == 'flat' and not sg:
            if not q_tag_value:
                q_tag_value = ''
            q_tag_value += tag['Key'] + ': ' + tag['Value'] + ","
        elif q_tag == 'flat' and sg == "sg":
            if not q_tag_value:
                q_tag_value = ''
            q_tag_value += tag['GroupName'] + ': ' + tag['GroupId'] + ","
        else:
            if tag['Key'].casefold() == q_tag.casefold():
                q_tag_value = tag['Value']
                if tag['Value'] == 'True'.casefold() or tag['Value'] == "yes".casefold() or tag['Value'] == "y".casefold():
                    q_tag_value = True
                if tag['Value'] == 'False'.casefold() or tag['Value'] == 'no'.casefold() or tag['Value'] == "n".casefold():
                    q_tag_value = False
                break
    return q_tag_value


def vpc_data(vpcid, q_tag, response_vpc):
    q_tag_value = False
    for vpc in response_vpc['Vpcs']:
        if vpcid == vpc['VpcId']:
            if vpc.get('Tags', False):
                if q_tag == "flat":
                    for tag in vpc.get('Tags'):
                        if "iTerm" in tag['Key'] or 'Cloud_Profiler' in tag['Key']:
                            if not q_tag_value:
                                q_tag_value = ''
                            q_tag_value += "VPC." + tag['Key'] + ': ' + tag['Value'] + ","
                else:
                    q_tag_value = get_tag_value(vpc.get('Tags'), q_tag)
    return q_tag_value

def getDOInstances(profile):
    instance_source = "DO." + profile['name']
    groups = {}
    instances = {}
    global instance_counter
        
    instance_counter[instance_source] = 0
    manager = digitalocean.Manager(token=profile['token'])
    my_droplets = manager.get_all_droplets()

    for drop in my_droplets:
        if (script_config['DO'].get('Skip_stopped', True) == True \
            and script_config['Local'].get('Skip_stopped', True) == True \
            and profile.get('Skip_stopped', True) == True) \
            and drop.status != 'active':
            continue
        
        Password = [False, ""]
        Iterm_tags = []
        Instance_use_Ip_public = settingResolver('Use_Ip_public',drop, {}, "DO", True)
        Instance_use_Bastion = settingResolver('Use_bastion',drop, {}, "DO", False)
        Or_host_name=settingResolver('Host_name',drop,{},"DO", False)
        Bastion = settingResolver('Bastion',drop,{},"DO", False)
        Con_username = settingResolver('Con_username',drop,{},"DO", False)
        Bastion_Con_username = settingResolver('Bastion_Con_username',drop,{},"DO", False)
        Con_port = settingResolver('Con_port',drop,{},"DO", 22)
        Bastion_Con_port = settingResolver('Bastion_Con_port',drop,{},"DO", 22)
        SSH_key = settingResolver('SSH_key',drop,{}, "DO", False)
        Use_shared_key = settingResolver('Use_shared_key',drop,{},"DO", False)
        Login_command = settingResolver('Login_command',drop,{},"DO", False)
        Dynamic_profile_parent_name = settingResolver('Dynamic_profile_parent_name',drop,{},"DO")
        Public_ip = drop.ip_address

        if Or_host_name:
            drop_name = Or_host_name
        else:
            drop_name = drop.name

        if Instance_use_Ip_public:
            ip = drop.ip_address
        else:
            ip = drop.private_ip_address
            
        if drop.name in drop.tags:
            groups[drop.name] = groups[drop.name] + 1
        else:
            groups[drop.name] = 1

        if drop.tags:
            for tag in drop.tags:
                if tag:
                    Iterm_tags.append(tag)
        
        Iterm_tags += f"ip: {ip}",f"Name: {drop.name}"
        instances[ip] = {'Name':instance_source + '.' + drop_name,
                        'Group': drop_name,
                        'Index':groups[drop.name],
                        'Dynamic_profile_parent_name': Dynamic_profile_parent_name,
                        'Iterm_tags': Iterm_tags, 'InstanceType': drop.size['slug'],
                        'Con_username': Con_username,
                        'Bastion_Con_username': Bastion_Con_username,
                        'Con_port': Con_port,
                        'Bastion_Con_port': Bastion_Con_port,
                        'Id': drop.id,
                        'SSH_key': SSH_key,
                        'Use_shared_key': Use_shared_key,
                        'Login_command': Login_command,
                        'Instance_use_Bastion': Instance_use_Bastion,
                        'Bastion': Bastion,
                        'Instance_use_Ip_public': Instance_use_Ip_public,
                        'Ip_public': Public_ip,
                        'Password': Password,
                        'Region': drop.region['name']}
        print(f'instance_source: {ip}\t\t{instance_source}. {drop_name}\t\tassociated Bastion: "{str(Bastion)}"')
    
    cloud_instances_obj_list.append({"instance_source": instance_source, "groups": groups, "instances":instances})

def fetchEC2Instance(instance, client, groups, instances, instance_source, reservation, vpc_data_all):
    instance_vpc_flat_tags = ''
    instance_flat_tags = ''
    Iterm_tags = []
    Password = [False, ""]

    Instance_use_Bastion = settingResolver('Use_bastion', instance, vpc_data_all,'AWS', False)
    Instance_use_Ip_public = settingResolver('Use_Ip_public', instance, vpc_data_all,'AWS', False)
    SSH_key = settingResolver('SSH_key', instance, vpc_data_all,'AWS', instance.get('KeyName',False))
    Use_shared_key = settingResolver('Use_shared_key', instance, vpc_data_all,'AWS', False)
    Login_command = settingResolver('Login_command', instance, vpc_data_all,'AWS', False)
    Con_username = settingResolver('Con_username', instance, vpc_data_all,'AWS', False)
    Bastion_Con_username = settingResolver('Bastion_Con_username', instance, vpc_data_all,'AWS', False)
    Con_port = settingResolver('Con_port', instance, vpc_data_all,'AWS', 22)
    Bastion_Con_port = settingResolver('Bastion_Con_port', instance, vpc_data_all,'AWS', 22)
    Bastion = settingResolver("Bastion", instance, vpc_data_all,'AWS', False)
    Dynamic_profile_parent_name = settingResolver('Dynamic_profile_parent_name', instance, vpc_data_all,'AWS', False)
    instance_vpc_flat_tags = vpc_data(instance.get('VpcId', ''), "flat", vpc_data_all)
    instance_flat_sgs = ''
    for interface in instance.get('NetworkInterfaces',[]):
        instance_flat_sgs += (get_tag_value(interface['Groups'],'flat',"sg"))
    
    if not SSH_key:
        SSH_key = instance.get('KeyName', '')

    if 'Tags' in instance:
        name = get_tag_value(instance['Tags'], "Name" ,False, instance['InstanceId'])
        instance_flat_tags = get_tag_value(instance['Tags'], 'flat')
    else:
        name = instance['InstanceId']

    if Instance_use_Ip_public == True and 'PublicIpAddress' in instance:
        ip = instance['PublicIpAddress']
    else:
        try:
            ip = instance['NetworkInterfaces'][0]['PrivateIpAddress']
        except IndexError:
            ip = "No IP found at scan time ¯\_(ツ)_/¯, probably a terminated instance. (Sorry)#"

    if name in groups:
        groups[name] = groups[name] + 1
    else:
        groups[name] = 1

    if 'PublicIpAddress' in instance:
        Public_ip = instance['PublicIpAddress']
        Iterm_tags.append(f"Ip_public: {instance['PublicIpAddress']}")
    else:
        Public_ip = ''
    
    if instance_flat_tags:
        Iterm_tags.append(instance_flat_tags)
    if instance_vpc_flat_tags:
        Iterm_tags.append(instance_vpc_flat_tags)
    if instance_flat_sgs:
        Iterm_tags.append(instance_flat_sgs)

    Iterm_tags.append(f"VPC: {instance.get('VpcId','')}")
    Iterm_tags.append(f"Id: {instance['InstanceId']}")
    Iterm_tags.append(f"AvailabilityZone: {instance['Placement']['AvailabilityZone']}")
    Iterm_tags.append(f"InstanceType: {instance['InstanceType']}")
    if instance['PublicDnsName']:
        Iterm_tags.append(f"PublicDnsName: {instance['PublicDnsName']}")
    if instance['PrivateDnsName']:
        Iterm_tags.append(f"PrivateDnsName: {instance['PrivateDnsName']}")
    if instance['ImageId']:
        Iterm_tags.append(f"ImageId: {instance['ImageId']}")
    
    Iterm_tags_fin = []
    for tag in Iterm_tags:
        if ',' in tag:
            for shard in tag.split(','):
                if shard.strip():
                    Iterm_tags_fin.append(shard)
        else:
            Iterm_tags_fin.append(tag)
    
    
    if instance.get('Platform', '') == 'windows':
        response =  client.get_password_data(
                    InstanceId=instance['InstanceId'],
                    )
        data = base64.b64decode(response['PasswordData'])
        Password = decrypt(data, os.path.join(script_config["Local"].get('SSH_keys_path', '.'),SSH_key))
    
    instances[ip] = {'Name': instance_source + '.' + name,
                     'Index': groups[name],
                     'Group': name,
                     'Bastion': Bastion,
                     'VPC': instance.get('VpcId', ""),
                     'Instance_use_Ip_public': Instance_use_Ip_public,
                     'Instance_use_Bastion': Instance_use_Bastion,
                     'Ip_public': Public_ip,
                     'Dynamic_profile_parent_name': Dynamic_profile_parent_name, 'Iterm_tags': Iterm_tags_fin,
                     'InstanceType': instance['InstanceType'],
                     'Con_username': Con_username,
                     'Bastion_Con_username': Bastion_Con_username,
                     'Con_port': Con_port,
                     'Bastion_Con_port': Bastion_Con_port,
                     'Id': instance['InstanceId'],
                     'SSH_key': SSH_key,
                     'Use_shared_key': Use_shared_key,
                     'Login_command': Login_command,
                     'Platform': instance.get('Platform', ''),
                     'Password': Password,
                     'Region': instance['Placement']['AvailabilityZone'][:-1]}
    return (ip + "\t" + instance['Placement']['AvailabilityZone'] + "\t" + instance_source + "." + name + "\t\t associated Bastion: \"" + str(Bastion) + "\"")


def fetchEC2Region(region, profile_name, instances, groups, instance_source, credentials = False):
    if region in script_config['AWS']['exclude_regions']:
        print(f'{instance_source}: region "{region}", is in excluded list')
        return

    if credentials:
        client = boto3.client('ec2',
                            aws_access_key_id=credentials['AccessKeyId'],
                            aws_secret_access_key=credentials['SecretAccessKey'],
                            aws_session_token=credentials['SessionToken'],
                            region_name=region)
    else:
        client = boto3.client('ec2', region_name=region)

    if script_config['AWS'].get('Skip_stopped', True) == False or script_config['Local'].get('Skip_stopped', True) == False or profile.get('Skip_stopped', True) == False:
        search_states = ['running', 'pending', 'shutting-down', 'terminated', 'stopping', 'stopped']
    else:
        search_states = ['running']

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
                if script_config["Local"].get('Parallel_exec', True):
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(fetchEC2Instance, instance, client, groups, instances, instance_source, reservation, vpc_data_all)
                        return_value = future.result()
                        print(f'{instance_source}: {return_value}')
                else:
                    print(fetchEC2Instance(instance, client, groups, instances, instance_source, reservation, vpc_data_all))
    else:
        print(f'{instance_source}: No instances found in {region}')

def get_MFA_func():
    try:
        retry = 3
        while retry > 0:
            mfa_TOTP = inputimeout(prompt=f"Note: The MFA code must be uniq for each account," \
                                    f' so wait until it rotates before entering it for each account...\n' \
                                    f'Enter your MFA code for "{profile["name"]}", so you can assume the role "{profile["role_arns"][role_arn].rpartition("/")[2]}"' \
                                    f' in "{role_arn}": ',
                                    timeout=30
                                    )
            if (not mfa_TOTP.isnumeric() or len(mfa_TOTP) != 6) and retry > 1:
                print(f"Sorry, MFA can only be 6 numbers.\nPlease try again.")
            elif retry == 1:
                print(f"Maximum amount of failed attempts reached, so skipping {role_arn}.")
                return
            else:
                return mfa_TOTP
            retry -= 1
    except TimeoutOccurred:
        print(f"Input not supplied within allowed amount of time, skipping {role_arn}.")
        return False

def getEC2Instances(profile, role_arn = False):
    groups = {}
    instances = {}
    credentials = False
    global instance_counter

    if isinstance(profile,dict):
        instance_source = "aws." + profile['name']
        profile_name = profile['name']
        boto3.setup_default_session(aws_access_key_id=profile['aws_access_key_id'],aws_secret_access_key=profile['aws_secret_access_key'],region_name="eu-central-1")
    else:
        instance_source = "aws." + profile
        boto3.setup_default_session(profile_name=profile,region_name="eu-central-1")
        profile_name = profile

    if role_arn:
        instance_source = f"{instance_source}.{role_arn}"
        role_session_name = f"{os.path.basename(__file__).rpartition('.')[0]}."\
                            f"{getpass.getuser().replace(' ','_')}@{platform.uname()[1]}"
        sts_client = boto3.client('sts')
        if profile.get("MFA_serial_number", False):
            retry = 3
            while retry > 0:
                try:
                    assumed_role_object=sts_client.assume_role(
                                        RoleArn=profile["role_arns"][role_arn],
                                        RoleSessionName=role_session_name,
                                        DurationSeconds=3600,
                                        SerialNumber=profile["mfa_serial_number"],
                                        TokenCode=get_MFA_func()
                    )
                    if assumed_role_object['ResponseMetadata']['HTTPStatusCode'] == 200:
                        break
                except:
                    retry -= 1
                    if retry == 0:
                        print(f'Sorry, was unable to "login" to {profile_name} using STS + MFA.')
                        return
                    else:
                        pass
        else:
            try:
                assumed_role_object=sts_client.assume_role(
                                    RoleArn=profile["role_arns"][role_arn],
                                    RoleSessionName=role_session_name
                )
            except Exception as e:
                print(f"The exception was:\n{e}")
                return

        credentials=assumed_role_object['Credentials']
        client = boto3.client('ec2',
                                aws_access_key_id=credentials['AccessKeyId'],
                                aws_secret_access_key=credentials['SecretAccessKey'],
                                aws_session_token=credentials['SessionToken'])
    else:
        client = boto3.client('ec2')
    instance_counter[instance_source] = 0
    
    try:
        ec2_regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    except:
        print(f'Was unable to retrive information for "regions" in account "{profile_name}", so it was skipped.')
        return

    if script_config["Local"].get('Parallel_exec', True):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            [executor.submit(fetchEC2Region, region , profile_name, instances, groups, instance_source, credentials) for region in ec2_regions]
    else:
        for region in ec2_regions:
            fetchEC2Region(region , profile_name, instances, groups, instance_source, credentials)

    for ip in instances:
        instance = instances[ip]
        instance['Name'] = instance['Name'] + str(instance['Index']) if groups[instance['Group']] > 1 else instance['Name']
    
    cloud_instances_obj_list.append({"instance_source": instance_source, "groups": groups, "instances":instances})


def updateMoba(dict_list):
    global instance_counter
    bookmark_counter = 1

    d = ''
    for d in dict_list:
        if not 'instance_by_region' in d:
            d['instance_by_region'] = {}
        for key,instance in d['instances'].items():
            if not instance['Region'] in d['instance_by_region']:
                d['instance_by_region'][instance['Region']] = []
            instance['ip'] = key
            d['instance_by_region'][instance['Region']].append(instance)
    del d


    profiles = "[Bookmarks]\nSubRep=\nImgNum=42"
    
    for profile_dict in dict_list:
        for region in profile_dict['instance_by_region']:
            profiles +=  f"""\n[Bookmarks_{bookmark_counter}]\nSubRep={profile_dict["instance_source"]}\\{region}\nImgNum=41\n"""
            for instance in profile_dict['instance_by_region'][region]:
                instance_counter[profile_dict['instance_source']] += 1
                shortName = instance['Name'].rpartition('.')[2]
                group = instance['Group']

                connection_command = f"{shortName}= "

                tags = ["Account: " + profile_dict["instance_source"], str(instance['Id'])]
                for tag in instance['Iterm_tags']:
                    tags.append(tag)
                if profile_dict["groups"].get(group, 0) > 1:
                    tags.append(group)


                if "Sorry" in instance:
                    connection_command = "echo"
                    ip_for_connection = instance
                elif instance.get('Instance_use_Ip_public', False) == True or not instance['Bastion']:
                    ip_for_connection = instance['Ip_public']
                else:
                    ip_for_connection = instance['ip']


                if instance['Con_username']:
                    Con_username = instance['Con_username']
                else:
                    Con_username = '<default>'
                
                if instance.get('Platform', '') == 'windows':
                    if not instance['Con_username']:
                        Con_username = "Administrator"
                    connection_type = "#91#4%"
                else:
                    connection_type = "#109#0%"
                
                if ( instance['Bastion'] != False \
                    and instance['Instance_use_Ip_public'] != True ) \
                    or instance['Instance_use_Bastion'] == True:
                    
                    Bastion_for_profile = instance['Bastion']
                else:
                    Bastion_for_profile = ''

                if instance['SSH_key'] and instance['Use_shared_key']:
                    sharead_key_path = os.path.join(connection_command,os.path.expanduser(script_config["Local"].get('SSH_keys_path', '.')), instance['SSH_key'])
                else:
                        sharead_key_path = ''
                tags = ','.join(tags)
                if instance['Bastion_Con_port'] != 22:
                    Bastion_port = instance['Bastion_Con_port']
                else:
                    Bastion_port = ''
                if instance['Bastion_Con_username']:
                    Bastion_user = instance['Bastion_Con_username']
                else:
                    Bastion_user = ''
                if instance['Login_command']:
                    login_command = instance['Login_command']
                else:
                    login_command = ''
                profile =   (
                        f"\n{shortName}= {connection_type}{ip_for_connection}%{instance['Con_port']}%"
                        f"{Con_username}%%-1%-1%{login_command}%{Bastion_for_profile}%{Bastion_port}%{Bastion_user}%0%"
                        f"0%0%{sharead_key_path}%%"
                        f"-1%0%0%0%%1080%%0%0%1#MobaFont%10%0%0%0%15%236,"
                        f"236,236%30,30,30%180,180,192%0%-1%0%%xterm%-1%"
                        f"-1%_Std_Colors_0_%80%24%0%1%-1%<none>%%0#0# {tags}\n"
                )
                profiles += profile
            bookmark_counter += 1

    handle = open(os.path.expanduser(os.path.join(CP_OutputDir,'Cloud-profiler-Moba.mxtsessions')),'wt')
    handle.write(profiles)
    handle.close()



def updateTerm(dict_list):
    global instance_counter

    for profile_dict in dict_list:
        profiles = []
        for instance in profile_dict['instances']:
            instance_counter[profile_dict['instance_source']] += 1
            group = profile_dict["instances"][instance]['Group']

            connection_command = "ssh"
            # Con_username = ''

            tags = ["Account: " + profile_dict["instance_source"], instance]
            for tag in profile_dict["instances"][instance]['Iterm_tags']:
                tags.append(tag)
            if profile_dict["groups"].get(group, 0) > 1:
                tags.append(group)


            if "Sorry" in instance:
                connection_command = "echo"
                ip_for_connection = instance
            elif profile_dict["instances"][instance].get('Instance_use_Ip_public', False) == True or not profile_dict["instances"][instance]['Bastion']:
                ip_for_connection = profile_dict["instances"][instance]['Ip_public']
            else:
                ip_for_connection = instance

            
            if profile_dict["instances"][instance].get('platform', False) == 'windows':
                if not profile_dict["instances"][instance]['Con_username']:
                    Con_username = "Administrator"

            connection_command = f"{connection_command} {ip_for_connection}"
            
            if profile_dict["instances"][instance]['Bastion'] != False \
                and profile_dict["instances"][instance]['Instance_use_Ip_public'] != True \
                or profile_dict["instances"][instance]['Instance_use_Bastion'] == True:
                
                Bastion_connection_command = ''

                if profile_dict['instances'][instance]['Bastion_Con_username']:
                    Bastion_connection_command =    f"{profile_dict['instances'][instance]['Bastion_Con_username']}@" \
                                                    f"{profile_dict['instances'][instance]['Bastion']}"
                else:
                    Bastion_connection_command =    f"{profile_dict['instances'][instance]['Bastion']}"
                
                if profile_dict['instances'][instance]['Bastion_Con_port'] and profile_dict['instances'][instance]['Bastion_Con_port'] != 22:
                    Bastion_connection_command = f"{Bastion_connection_command}:{profile_dict['instances'][instance]['Bastion_Con_port']}"
                
                connection_command = f"{connection_command} -J {Bastion_connection_command}"
                
                if profile_dict["instances"][instance]['Con_username'] == False and profile_dict["instances"][instance].get('Platform', False) == 'windows':
                
                    connection_command = f"function random_unused_port {{ local port=$( echo $((2000 + ${{RANDOM}} % 65000))); (echo " \
                                    f">/dev/tcp/127.0.0.1/$port) &> /dev/null ; if [[ $? != 0 ]] ; then export " \
                                    f"RANDOM_PORT=$port; else random_unused_port ;fi }}; " \
                                    f"if [[ -n ${{RANDOM_PORT+x}} && -n \"$( ps aux | grep \"ssh -f\" | grep -v grep | awk \'{{print $2}}\' )\" ]]; " \
                                    f" then kill -9 $( ps aux | grep \"ssh -f\" | grep -v grep | awk \'{{print $2}}\' ) ; else random_unused_port; fi ;ssh -f -o " \
                                    f"ExitOnForwardFailure=yes -L ${{RANDOM_PORT}}:{ip_for_connection}:" \
                                    f"{profile_dict['instances'][instance].get('Con_port_windows', 3389)} " \
                                    f"{Bastion_connection_command} sleep 10 ; open " \
                                    f"'rdp://full%20address=s:127.0.0.1:'\"${{RANDOM_PORT}}\"'" \
                                    f"&audiomode=i:2&disable%20themes=i:0&screen%20mode%20id=i:1&use%20multimon" \
                                    f":i:0&username:s:{Con_username}" \
                                    f"&desktopwidth=i:1024&desktopheight=i:768'"
            elif profile_dict["instances"][instance].get('Platform', False) == 'windows':
                Con_username = profile_dict["instances"][instance]['Con_username']
                connection_command = f"open 'rdp://full%20address=s:{ip_for_connection}:{profile_dict['instances'][instance].get('Con_port_windows', 3389)}" \
                                f"&audiomode=i:2&disable%20themes=i:0&screen%20mode%20id=i:1&use%20multimon" \
                                f":i:0&username:s:{Con_username}" \
                                f"&desktopwidth=i:1024&desktopheight=i:768'"

            if profile_dict["instances"][instance]['Password'][0] and profile_dict["instances"][instance].get('Platform', '') == 'windows':
                    connection_command =    f"echo \"\\nThe Windows password on record is:\\n{profile_dict['instances'][instance]['Password'][1].rstrip()}\\n\\n\" " \
                                            f"\;echo -n '{profile_dict['instances'][instance]['Password'][1].rstrip()}' | pbcopy; " \
                                            f'echo \"\\nIt has been sent to your clipboard for easy pasting\\n\\n\";{connection_command}'

            elif profile_dict["instances"][instance].get('Platform', '') == 'windows':
                    connection_command =    f'echo \"\\nThe Windows password could not be decrypted...\\n' \
                                            f"The only hint we have is:{connection_command}\\n\\n\";\n{str(profile_dict['instances'][instance]['Password'][1])}"

            if profile_dict["instances"][instance].get('Platform', '') != 'windows':
                connection_command = f"{connection_command} {script_config['Local']['SSH_base_string']}"

                if profile_dict["instances"][instance]['Con_username']:
                    connection_command = f"{connection_command} -l {profile_dict['instances'][instance]['Con_username']}"
            
                if profile_dict["instances"][instance]['Con_port']:
                    connection_command = f"{connection_command} -p {profile_dict['instances'][instance]['Con_port']}"

                if profile_dict["instances"][instance]['SSH_key'] and profile_dict["instances"][instance]['Use_shared_key']:
                    connection_command = f"{connection_command} -i {script_config['Local'].get('SSH_keys_path', '.')}/{profile_dict['instances'][instance]['SSH_key']}"

                if profile_dict["instances"][instance]['Login_command']:
                    connection_command = f"{connection_command} -t {profile_dict['instances'][instance]['Login_command']}"
            
            if profile_dict["instances"][instance]['Dynamic_profile_parent_name']:
                Dynamic_profile_parent_name = profile_dict["instances"][instance]['Dynamic_profile_parent_name']
            else:
                Dynamic_profile_parent_name = 'Default'
                
            profile = {"Name":profile_dict["instances"][instance]['Name'],
                        "Guid":f"{profile_dict['instance_source']}-{str(profile_dict['instances'][instance]['Id'])}",
                        "Badge Text": f"{BadgeMe(instance, profile_dict['instances'][instance])}",
                        "Tags":tags,
                        "Dynamic Profile Parent Name": Dynamic_profile_parent_name,
                        "Custom Command" : "Yes",
                        "Initial Text" : connection_command
                        }

            profiles.append(profile)

        profiles = {"Profiles":(profiles)}
        handle = open(os.path.expanduser(os.path.join(CP_OutputDir,"." + profile_dict["instance_source"])),'wt')
        handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
        handle.close()
        head_tail = os.path.split(handle.name)
        rename_tagret = head_tail[1][1:]
        os.rename(handle.name,os.path.join(head_tail[0],rename_tagret))


def update_statics():
    profiles =[]
    app_static_profile_handle = open(os.path.expanduser(os.path.join(CP_OutputDir, ".statics")),"wt")
    path_to_Static_profiles = os.path.expanduser(script_config["Local"]['Static_profiles'])
    
    for root, dirs, files in os.walk(path_to_Static_profiles, topdown=False):
        for name in files:
            if name == '.DS_Store':
                print(f'Static profiles, skipping ".DS_Store"')
                continue
            print(f'Working on static profile: {name}')
            static_profile_handle=open(os.path.join(root, name))
            profiles.append(json.load(static_profile_handle))

    
    profiles = {"Profiles":(profiles)} 
    app_static_profile_handle.write(json.dumps(profiles,sort_keys=True,indent=4, separators=(',', ': ')))
    app_static_profile_handle.close()
    shutil.move(app_static_profile_handle.name,os.path.expanduser(os.path.join(CP_OutputDir, "statics")))



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
    file = open("marker.tmp", "w") 
    file.write("mark") 
    file.close() 
    instance_counter = {}
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cloud_instances_obj_list = []

    # From repo
    with open(os.path.join(script_dir,'config.yaml')) as conf_file:
        script_config_repo = yaml.full_load(conf_file)
    
    if os.environ.get('CP_OutputDir', False):
        CP_OutputDir = os.environ['CP_OutputDir']
    elif platform.system() == 'Windows' or os.environ.get('CP_Windows', False):
        CP_OutputDir = "~/Cloud_Profiler/"
    else:
        CP_OutputDir = "~/Library/Application Support/iTerm2/DynamicProfiles/"
    print(f"CP_OutputDir to be used: {CP_OutputDir}")
    
    if not os.path.isdir(os.path.expanduser(CP_OutputDir)):
        os.makedirs(os.path.expanduser(CP_OutputDir))

    # From user home direcotry
    script_config = {}
    script_config_user = {}
    if os.path.isfile(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")):
        print("Found conf file in place")
        with open(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")) as conf_file:
            script_config_user = yaml.full_load(conf_file)
    else:
        if not os.path.isdir(os.path.expanduser("~/.iTerm-cloud-profile-generator/")):
            os.makedirs(os.path.expanduser("~/.iTerm-cloud-profile-generator/"))
        shutil.copy2(os.path.join(script_dir,'config.yaml'), os.path.expanduser("~/.iTerm-cloud-profile-generator/"))
        print(f"Copy defualt config to home dir {os.path.expanduser('~/.iTerm-cloud-profile-generator/')}")


    for key in script_config_repo:
        script_config[key] = {**script_config_repo.get(key, {}),**script_config_user.get(key, {})}


    username = getpass.getuser()
    config = configparser.ConfigParser()

    # Static profiles iterator
    update_statics()

    # AWS profiles iterator
    if script_config['AWS'].get('profiles', False):
        for profile in script_config['AWS']['profiles']:
            print(f"Working on {profile['name']}")
            if isinstance(profile.get("role_arns", False),dict):
                for role_arn in profile["role_arns"]:
                    getEC2Instances(profile, role_arn)
            else:
                getEC2Instances(profile)
            
    # AWS profiles iterator from config file
    if script_config['AWS'].get('use_awscli_profiles', False):
        if os.path.exists(os.path.expanduser(script_config['AWS']['aws_credentials_file'])):
            config.read(os.path.expanduser(script_config['AWS']['aws_credentials_file']))
            for i in config.sections():
                if i not in script_config['AWS']['exclude_accounts']:
                    print(f'Working on AWS profile from credentials file: {i}')
                    getEC2Instances(i)
    
    # DO profiles iterator
    if script_config['DO'].get('profiles', False):
        for profile in script_config['DO']['profiles']:
            print(f"Working on {profile['name']}")
            getDOInstances(profile)
    
    if platform.system() == 'Windows' or os.environ.get('CP_Windows', False):
        updateMoba(cloud_instances_obj_list)
    else:
        updateTerm(cloud_instances_obj_list)
    
    if os.path.exists('marker.tmp'):
        os.remove("marker.tmp")
    print(f"\nCreated profiles {json.dumps(instance_counter,sort_keys=True,indent=4, separators=(',', ': '))}\nTotal: {sum(instance_counter.values())}")
    print(f"\nWe wish you calm clouds and a serene path...\n")