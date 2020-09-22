#!/usr/local/bin/python
# coding: UTF-8

import base64
import concurrent.futures
import configparser
import getpass
import json
import multiprocessing as mp
import os
import platform
import shutil
import subprocess
from typing import Union, Dict, Any

import boto3
import digitalocean
import yaml
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from inputimeout import inputimeout, TimeoutOccurred
from sshconf import empty_ssh_config_file


class InstanceProfile:
    """This is an instance profile"""
    def __init__(self):
        self.iterm_tags_fin = []
        self.Name = ""
        self.Group = ""
        self.Index = 0
        self.Dynamic_profile_parent_name = ""
        self.iterm_tags = ""
        self.Con_username = ""
        self.Bastion_Con_username = ""
        self.Con_port = 22
        self.Bastion_Con_port = 22
        self.Id = 0
        self.SSH_key = ""
        self.Use_shared_key = False
        self.Login_command = ""
        self.Instance_use_Bastion = False
        self.Bastion = ""
        self.instance_use_ip_public = False
        self.Ip_public = ""
        self.Password = ""
        self.Region = ""
        self.Docker_contexts_create = False
        self.instance_source = ""
        self.instance_flat_sgs = ""
        self.instance_flat_tags = ""
        self.iterm_tags = []

    def iterm_tags_fin_constructor(self):
        for tag in self.iterm_tags:
            if ',' in tag:
                for shard in tag.split(','):
                    if shard.strip():
                        self.iterm_tags_fin.append(shard)
            else:
                self.iterm_tags_fin.append(tag)


example_obj = InstanceProfile()
example_obj.iterm_tags = 'common_-_grafana: sg-0667450a2a83d23cf,grafana: sg-0e443333e2fb81cb1,hyver-internal: sg-1c456166,Access from Jumphost or Jenkins slave: sg-04a357a3b336e91f9,staging_grafana: sg-045910b86c64b4b89,'
print(example_obj.iterm_tags_fin_constructor())


def line_prepender(filename, line):
    with open(filename, 'r+') as file_to_append_to:
        content = file_to_append_to.read()
        file_to_append_to.seek(0, 0)
        file_to_append_to.write(line.rstrip('\r\n') + '\n' + content)


def badgeme(instance_key, instance):
    end_badge = []
    name = instance['Name'].split('.')
    if len(name) == 4:
        name_formatted = f"Instance name: {name[3]} \n" \
                         f"Cloud provider: {name[0]} \n Cloud account: {name[2]}" \
                         f"Account profile: {name[1]}"
    else:
        name_formatted = f"Instance name: {name[2]}" \
                         f"Cloud provider: {name[0]}" \
                         f"Account profile: {name[1]}"
    all_badge_toggles = script_config["Local"].get("Badge_info_to_display", None)
    if not all_badge_toggles:
        value_to_return = f"{name_formatted}" \
                          f"InstanceType: {instance['InstanceType']}" \
                          f"Ip_public: {instance['Ip_public']}" \
                          f"Main_IP: {instance_key}"
    else:
        for [badge, toggle] in all_badge_toggles.items():
            if toggle or isinstance(toggle, list):
                if badge == "Instance_key":
                    end_badge.append(f"Main_IP: {instance_key}")
                if badge == "name" and toggle == "Formatted":
                    end_badge.append(f"{name_formatted}")
                    continue
                if badge and instance['Password'][1] != "":
                    end_badge.append(f"{badge}: {instance['Password'][1]}")
                if instance.get(badge, False) and badge != "password":
                    end_badge.append(f"{badge}: {str(instance[badge])}")
                if isinstance(toggle, list) and len(toggle) != 0:
                    end_badge.append(q_tag_flat(instance['iterm_tags'], toggle))
                if isinstance(toggle, list) and len(toggle) == 0:
                    end_badge.append(f"{instance['iterm_tags']}")
        value_to_return = '\n'.join(filter(lambda x: x != "", end_badge))
    return value_to_return


def q_tag_flat(tags, badge_tag_to_display):
    return_value = []
    for tag in tags:
        if tag.split(':')[0] in badge_tag_to_display:
            return_value.append(tag)
    return_value_formatted = f"iTerm tags: {', '.join(filter(lambda x: x != '', return_value))}"
    return return_value_formatted


# noinspection PyTypeChecker
def decrypt(ciphertext, keyfile):
    if not os.path.isfile(os.path.expanduser(keyfile)):
        return [False, f"Decryption key not found at {keyfile}."]
    with open(os.path.expanduser(keyfile)) as finput:
        fkey = RSA.importKey(finput.read())
    cipher = PKCS1_v1_5.new(fkey)
    plaintext = cipher.decrypt(ciphertext).decode('utf-8')
    return [True, plaintext]


def setting_resolver(
        setting: str,
        instance: any,
        vpc_data_all: dict,
        caller_type: object = 'AWS',
        setting_value: Union[dict, int, str, bool] = None,
        profile: dict = None,
        resolver_script_config: dict = None
) -> Union[dict, int, str, bool]:
    """

    :rtype: Union[dict, int, str, bool]
    """
    if profile is None:
        profile = []
    if setting_value is None:
        setting_value = {}
    if caller_type == 'AWS':
        setting_value = get_tag_value(instance.get('Tags', ''), setting, False, setting_value)
    if caller_type == 'DO':
        setting_value = get_do_tag_value(instance.tags, setting, setting_value)
    if not setting_value:
        if caller_type == 'AWS' and instance['State']['Name'] != "terminated":
            setting_value = vpc_data(instance['VpcId'], setting, vpc_data_all)
        if caller_type == 'DO':
            pass
        if not setting_value:
            if 'iTerm_' in setting:
                setting = setting.rpartition('iTerm_')[
                    2]  # Strip iTerm prefix because settings are now read from conf files
            if 'Cloud_Profiler_' in setting:
                setting = setting.rpartition('Cloud_Profiler_')[
                    2]  # Strip iTerm prefix because settings are now read from conf files
            setting_value = profile.get(setting, False)
            if not setting_value:
                setting_value = resolver_script_config[caller_type].get(setting, False)
                if not setting_value:
                    setting_value = resolver_script_config["Local"].get(setting, False)
    return setting_value


def get_do_tag_value(tags, q_tag, q_tag_value) -> Union[int, str]:
    for tag in tags:
        if ':' in tag and ('iTerm' in tag or 'Cloud_Profiler' in tags):
            tag_key, tag_value = tag.split(':')
            if tag_key == q_tag.casefold():
                q_tag_value = tag_value.replace('-', '.').replace('_', ' ')
                break
    return q_tag_value


def get_tag_value(tags, q_tag, sg=None, q_tag_value=False) -> Union[bool, int, str]:
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
                if tag['Value'] == 'True'.casefold() or tag['Value'] == "yes".casefold() or \
                        tag['Value'] == "y".casefold():
                    q_tag_value = True
                if tag['Value'] == 'False'.casefold() or tag['Value'] == 'no'.casefold() or \
                        tag['Value'] == "n".casefold():
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


def get_do_instances(profile, do_instance_counter, do_script_config, do_cloud_instances_obj_list):
    instance_source = "DO." + profile['name']
    groups = {}
    instances = {}
    # global instance_counter

    do_instance_counter[instance_source] = 0
    do_manager = digitalocean.Manager(token=profile['token'])
    my_droplets = do_manager.get_all_droplets()

    for drop in my_droplets:
        if (do_script_config['DO'].get('Skip_stopped', True)
            and do_script_config['Local'].get('Skip_stopped', True)
            and profile.get('Skip_stopped', True)) \
                and drop.status != 'active':
            continue

        password = [False, ""]
        iterm_tags = []
        docker_context = setting_resolver('Docker_contexts_create', drop, {}, "DO", False, profile, do_script_config)
        instance_use_ip_public = setting_resolver(
                                    'instance_use_ip_public', drop, {}, "DO", True, profile, do_script_config
                                    )
        instance_use_bastion = setting_resolver('Use_bastion', drop, {}, "DO", False, profile, do_script_config)
        or_host_name = setting_resolver('Host_name', drop, {}, "DO", False, profile, do_script_config)
        bastion = setting_resolver('Bastion', drop, {}, "DO", False, profile, do_script_config)
        con_username = setting_resolver('Con_username', drop, {}, "DO", False, profile, do_script_config)
        bastion_con_username = setting_resolver('Bastion_Con_username', drop, {}, "DO", False, profile,
                                                do_script_config)
        con_port = setting_resolver('Con_port', drop, {}, "DO", 22, profile, do_script_config)
        bastion_con_port = setting_resolver('Bastion_Con_port', drop, {}, "DO", 22, profile, do_script_config)
        ssh_key = setting_resolver('SSH_key', drop, {}, "DO", False, profile, do_script_config)
        use_shared_key = setting_resolver('use_shared_key', drop, {}, "DO", False, profile, do_script_config)
        login_command = setting_resolver('Login_command', drop, {}, "DO", False, profile, do_script_config)
        dynamic_profile_parent_name = setting_resolver('Dynamic_profile_parent_name', drop, {}, "DO", False, profile,
                                                       do_script_config)
        public_ip = drop.ip_address

        if or_host_name:
            drop_name = or_host_name
        else:
            drop_name = drop.name

        if instance_use_ip_public:
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
                    iterm_tags.append(tag)

        iterm_tags += f"ip: {ip}", f"Name: {drop.name}"
        instances[ip] = {
            'Name': instance_source + '.' + drop_name,
            'Group': drop_name,
            'Index': groups[drop.name],
            'Dynamic_profile_parent_name': dynamic_profile_parent_name,
            'iterm_tags': iterm_tags, 'InstanceType': drop.size['slug'],
            'Con_username': con_username,
            'Bastion_Con_username': bastion_con_username,
            'Con_port': con_port,
            'Bastion_Con_port': bastion_con_port,
            'Id': drop.id,
            'SSH_key': ssh_key,
            'Use_shared_key': use_shared_key,
            'Login_command': login_command,
            'Instance_use_Bastion': instance_use_bastion,
            'Bastion': bastion,
            'instance_use_ip_public': instance_use_ip_public,
            'Ip_public': public_ip,
            'Password': password,
            'Region': drop.region['name'],
            'Docker_contexts_create': docker_context
        }
        print(f'instance_source: {ip}\t\t{instance_source}. {drop_name}\t\tassociated bastion: "{str(bastion)}"')

    do_cloud_instances_obj_list.append({"instance_source": instance_source, "groups": groups, "instances": instances})


def fetch_ec2_instance(instance, client, groups, instances, instance_source, vpc_data_all, profile,
                       fetch_script_config):
    instance_flat_tags = ''
    iterm_tags = []
    password = [False, ""]

    docker_context = setting_resolver('docker_context', instance, vpc_data_all, 'AWS', False, profile,
                                      fetch_script_config)
    instance_use_bastion = setting_resolver('Use_bastion', instance, vpc_data_all, 'AWS', False, profile,
                                            fetch_script_config)
    instance_use_ip_public = setting_resolver('instance_use_ip_public', instance, vpc_data_all, 'AWS', False, profile,
                                              fetch_script_config)
    ssh_key = setting_resolver('SSH_key', instance, vpc_data_all, 'AWS', instance.get('KeyName', False), profile,
                               fetch_script_config)
    use_shared_key = setting_resolver('use_shared_key', instance, vpc_data_all, 'AWS', False, profile,
                                      fetch_script_config)
    login_command = setting_resolver('Login_command', instance, vpc_data_all, 'AWS', False, profile,
                                     fetch_script_config)
    con_username = setting_resolver('Con_username', instance, vpc_data_all, 'AWS', False, profile, fetch_script_config)
    bastion_con_username = setting_resolver('Bastion_Con_username', instance, vpc_data_all, 'AWS', False, profile,
                                            fetch_script_config)
    con_port = setting_resolver('Con_port', instance, vpc_data_all, 'AWS', 22, profile, fetch_script_config)
    bastion_con_port = setting_resolver('Bastion_Con_port', instance, vpc_data_all, 'AWS', 22, profile,
                                        fetch_script_config)
    bastion = setting_resolver("bastion", instance, vpc_data_all, 'AWS', False, profile, fetch_script_config)
    dynamic_profile_parent_name = setting_resolver('Dynamic_profile_parent_name', instance, vpc_data_all, 'AWS', False,
                                                   profile, fetch_script_config)
    instance_vpc_flat_tags = vpc_data(instance.get('VpcId', ''), "flat", vpc_data_all)
    instance_flat_sgs = ''
    for interface in instance.get('NetworkInterfaces', []):
        instance_flat_sgs += (get_tag_value(interface['Groups'], 'flat', "sg"))

    if not ssh_key:
        ssh_key = instance.get('KeyName', '')

    if 'Tags' in instance:
        name = get_tag_value(instance['Tags'], "Name", False, instance['InstanceId'])
        instance_flat_tags = get_tag_value(instance['Tags'], 'flat')
    else:
        name = instance['InstanceId']

    if instance_use_ip_public and 'PublicIpAddress' in instance:
        ip = instance['PublicIpAddress']
    else:
        try:
            ip = instance['NetworkInterfaces'][0]['PrivateIpAddress']
        except IndexError:
            ip = r'No IP found at scan time ¯\_(ツ)_/¯, probably a terminated instance. (Sorry)#'

    if name in groups:
        groups[name] = groups[name] + 1
    else:
        groups[name] = 1

    if 'PublicIpAddress' in instance:
        public_ip = instance['PublicIpAddress']
        iterm_tags.append(f"Ip_public: {instance['PublicIpAddress']}")
    else:
        public_ip = ''

    if instance_flat_tags:
        iterm_tags.append(instance_flat_tags)
    if instance_vpc_flat_tags:
        iterm_tags.append(instance_vpc_flat_tags)
    if instance_flat_sgs:
        iterm_tags.append(instance_flat_sgs)

    iterm_tags.append(f"VPC: {instance.get('VpcId', '')}")
    iterm_tags.append(f"Id: {instance['InstanceId']}")
    iterm_tags.append(f"AvailabilityZone: {instance['Placement']['AvailabilityZone']}")
    iterm_tags.append(f"InstanceType: {instance['InstanceType']}")
    if instance['PublicDnsName']:
        iterm_tags.append(f"PublicDnsName: {instance['PublicDnsName']}")
    if instance['PrivateDnsName']:
        iterm_tags.append(f"PrivateDnsName: {instance['PrivateDnsName']}")
    if instance['ImageId']:
        iterm_tags.append(f"ImageId: {instance['ImageId']}")

    iterm_tags_fin = []
    for tag in iterm_tags:
        if ',' in tag:
            for shard in tag.split(','):
                if shard.strip():
                    iterm_tags_fin.append(shard)
        else:
            iterm_tags_fin.append(tag)

    if instance.get('Platform', '') == 'windows':
        response = client.get_password_data(
            InstanceId=instance['InstanceId'],
        )
        data = base64.b64decode(response.get('passwordData', "U29ycnkgbm8ga2V5IHVzZWQgdG8gY3JlYXRlIFZNPw=="))
        password = decrypt(data, os.path.join(fetch_script_config["Local"].get('SSH_keys_path', '.'), ssh_key))

    instances[ip] = {
        'Name': instance_source + '.' + name,
        'Index': groups[name],
        'Group': name,
        'Bastion': bastion,
        'VPC': instance.get('VpcId', ""),
        'instance_use_ip_public': instance_use_ip_public,
        'Instance_use_Bastion': instance_use_bastion,
        'Ip_public': public_ip,
        'Dynamic_profile_parent_name': dynamic_profile_parent_name, 'iterm_tags': iterm_tags_fin,
        'InstanceType': instance['InstanceType'],
        'Con_username': con_username,
        'Bastion_Con_username': bastion_con_username,
        'Con_port': con_port,
        'Bastion_Con_port': bastion_con_port,
        'Id': instance['InstanceId'],
        'SSH_key': ssh_key,
        'use_shared_key': use_shared_key,
        'Login_command': login_command,
        'Platform': instance.get('Platform', ''),
        'Password': password,
        'Region': instance['Placement']['AvailabilityZone'][:-1],
        'docker_context': docker_context
    }
    return (ip + "\t" + instance['Placement'][
        'AvailabilityZone'] + "\t" + instance_source + "." + name + "\t\t associated bastion: \"" + str(bastion) + "\"")


def fetch_ec2_region(
        region,
        instances,
        groups,
        instance_source,
        credentials=None,
        profile=None,
        fetch_script_config=None
) -> None:
    if region in fetch_script_config['AWS']['exclude_regions']:
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

    if not fetch_script_config['AWS'].get('Skip_stopped', True) or \
            not fetch_script_config['Local'].get('Skip_stopped', True) \
            or not profile.get('Skip_stopped', True):
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

    if response.get('Reservations', False):
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        fetch_ec2_instance,
                        instance,
                        client,
                        groups,
                        instances,
                        instance_source,
                        vpc_data_all,
                        profile,
                        fetch_script_config
                    )
                    return_value = future.result()
                    print(f'{instance_source}: {return_value}')
    else:
        print(f'{instance_source}: No instances found in {region}')


def get_mfa_func(profile, mfa_role_arn):
    try:
        retry = 3
        while retry > 0:
            mfa_totp = inputimeout(
                prompt=f"Note: The MFA code must be unique for each account,"
                       f' so wait until it rotates before entering it for each account...\n'
                       f'Enter your MFA code for "{profile["name"]}", so you can assume the role "'
                       f'{profile["role_arns"][mfa_role_arn].rpartition("/")[2]}"'
                       f' in "{mfa_role_arn}": ',
                timeout=30
            )
            if (not mfa_totp.isnumeric() or len(mfa_totp) != 6) and retry > 1:
                print(f"Sorry, MFA can only be 6 numbers.\nPlease try again.")
            elif retry == 1:
                print(f"Maximum amount of failed attempts reached, so skipping {mfa_role_arn}.")
                return
            else:
                return mfa_totp
            retry -= 1
    except TimeoutOccurred:
        print(f"Input not supplied within allowed amount of time, skipping {mfa_role_arn}.")
        return False


def get_ec2_instances(
        profile: Union[dict, str] = None,
        ec2_role_arn: Union[int, slice] = None,
        ec2_instance_counter: dict = None,
        ec2_script_config: dict = None,
        ec2_cloud_instances_obj_list: list = None
) -> None:
    """

    :type ec2_instance_counter: dict
    :type ec2_role_arn: str
    :param ec2_cloud_instances_obj_list: list
    :param ec2_script_config:
    :param ec2_instance_counter:
    :param ec2_role_arn:
    :type profile: dict
    """
    groups = {}
    instances = {}
    credentials = False
    assumed_role_object = None

    if isinstance(profile, dict):
        instance_source = "aws." + profile['name']
        profile_name = profile['name']
        boto3.setup_default_session(aws_access_key_id=profile['aws_access_key_id'],
                                    aws_secret_access_key=profile['aws_secret_access_key'], region_name="eu-central-1")
    else:
        instance_source = "aws." + profile
        boto3.setup_default_session(profile_name=profile, region_name="eu-central-1")
        profile_name = profile

    if ec2_role_arn:
        instance_source = f"{instance_source}.{ec2_role_arn}"
        role_session_name = f"{os.path.basename(__file__).rpartition('.')[0]}." \
                            f"{getpass.getuser().replace(' ', '_')}@{platform.uname()[1]}"
        sts_client = boto3.client('sts')
        if profile.get("MFA_serial_number", False):
            retry = 3
            while retry > 0:
                try:
                    assumed_role_object = sts_client.assume_role(
                        RoleArn=profile["role_arns"][ec2_role_arn],
                        RoleSessionName=role_session_name,
                        DurationSeconds=3600,
                        SerialNumber=profile["mfa_serial_number"],
                        TokenCode=get_mfa_func(
                            profile,
                            profile["role_arns"][ec2_role_arn]
                        )
                    )
                    if assumed_role_object['ResponseMetadata']['HTTPStatusCode'] == 200:
                        break
                except Exception as e:
                    retry -= 1
                    if retry == 0:
                        print(f'Sorry, was unable to "login" to {profile_name} using STS + MFA.')
                        print(f"The exception was:\n{e}")
                        return
                    else:
                        pass
        else:
            try:
                assumed_role_object = sts_client.assume_role(
                    RoleArn=profile["role_arns"][ec2_role_arn],
                    RoleSessionName=role_session_name
                )
            except Exception as e:
                print(f"The exception was:\n{e}")
                return

        credentials = assumed_role_object['Credentials']
        client = boto3.client('ec2',
                              aws_access_key_id=credentials['AccessKeyId'],
                              aws_secret_access_key=credentials['SecretAccessKey'],
                              aws_session_token=credentials['SessionToken'])
    else:
        client = boto3.client('ec2')
    ec2_instance_counter[instance_source] = 0

    try:
        ec2_regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    except Exception as e:
        print(f'Was unable to retrieve information for "regions" in account "{profile_name}", so it was skipped.')
        print(f"The exception was:\n{e}")
        return

    for region in ec2_regions:
        fetch_ec2_region(
            region,
            instances,
            groups,
            instance_source,
            credentials,
            profile,
            ec2_script_config
        )

    for ip in instances:
        instance = instances[ip]
        instance['Name'] = instance['Name'] + str(instance['Index']) if groups[instance['Group']] > 1 else instance[
            'Name']

    ec2_cloud_instances_obj_list.append({"instance_source": instance_source, "groups": groups, "instances": instances})


def update_moba(dict_list):
    # global instance_counter
    bookmark_counter = 1

    for d in dict_list:
        if 'instance_by_region' in d:
            for dkey, instance in d['instances'].items():
                if not instance['Region'] in d['instance_by_region']:
                    d['instance_by_region'][instance['Region']] = []
                instance['ip'] = dkey
                d['instance_by_region'][instance['Region']].append(instance)
        else:
            d['instance_by_region'] = {}
    del d

    profiles = "[Bookmarks]\nSubRep=\nImgNum=42"

    for profile_dict in dict_list:
        for region in profile_dict['instance_by_region']:
            profiles += f"""\n[Bookmarks_{bookmark_counter}]
                        SubRep={profile_dict["instance_source"]}\\{region}\nImgNum=41\n"""
            for instance in profile_dict['instance_by_region'][region]:
                instance_counter[profile_dict['instance_source']] += 1
                short_name = instance['Name'].rpartition('.')[2]
                group = instance['Group']

                connection_command = f"{short_name}= "

                tags = ["Account: " + profile_dict["instance_source"], str(instance['Id'])]
                for tag in instance['iterm_tags']:
                    tags.append(tag)
                if profile_dict["groups"].get(group, 0) > 1:
                    tags.append(group)

                if "Sorry" in instance:
                    connection_command = "echo"
                    ip_for_connection = instance
                elif instance.get('instance_use_ip_public', False) or not instance['Bastion']:
                    ip_for_connection = instance['Ip_public']
                else:
                    ip_for_connection = instance['ip']

                if instance['Con_username']:
                    con_username = instance['Con_username']
                else:
                    con_username = '<default>'

                if instance.get('Platform', '') == 'windows':
                    if not instance['Con_username']:
                        con_username = "Administrator"
                    connection_type = "#91#4%"
                else:
                    connection_type = "#109#0%"

                if (instance['Bastion'] and not instance['instance_use_ip_public']) \
                        or instance['Instance_use_Bastion']:

                    bastion_for_profile = instance['Bastion']
                else:
                    bastion_for_profile = ''

                if instance['SSH_key'] and instance['use_shared_key']:
                    shard_key_path = os.path.join(connection_command, os.path.expanduser(
                        script_config["Local"].get('ssh_keys_path', '.')), instance['SSH_key'])
                else:
                    shard_key_path = ''
                tags = ','.join(tags)
                if instance['Bastion_Con_port'] != 22:
                    bastion_port = instance['Bastion_Con_port']
                else:
                    bastion_port = ''
                if instance['Bastion_Con_username']:
                    bastion_user = instance['Bastion_Con_username']
                else:
                    bastion_user = ''
                if instance['Login_command']:
                    login_command = instance['Login_command']
                else:
                    login_command = ''
                profile = (
                    f"\n{short_name}= {connection_type}{ip_for_connection}%{instance['Con_port']}%"
                    f"{con_username}%%-1%-1%{login_command}%{bastion_for_profile}%{bastion_port}%{bastion_user}%0%"
                    f"0%0%{shard_key_path}%%"
                    f"-1%0%0%0%%1080%%0%0%1#MobaFont%10%0%0%0%15%236,"
                    f"236,236%30,30,30%180,180,192%0%-1%0%%xterm%-1%"
                    f"-1%_Std_Colors_0_%80%24%0%1%-1%<none>%%0#0# {tags}\n"
                )
                profiles += profile
            bookmark_counter += 1

    with open(os.path.expanduser(os.path.join(CP_OutputDir, 'Cloud-profiler-Moba.mxtsessions')), 'wt') as handle:
        handle.write(profiles)


def update_term(dict_list):
    con_username = None

    for profile_dict in dict_list:
        profiles = []
        for instance in profile_dict['instances']:
            instance_counter[profile_dict['instance_source']] += 1
            group = profile_dict["instances"][instance]['Group']

            connection_command = "ssh"

            tags = ["Account: " + profile_dict["instance_source"], instance]
            for tag in profile_dict["instances"][instance]['iterm_tags']:
                tags.append(tag)
            if profile_dict["groups"].get(group, 0) > 1:
                tags.append(group)

            if "Sorry" in instance:
                connection_command = "echo"
                ip_for_connection = instance
            elif profile_dict["instances"][instance].get('instance_use_ip_public', False) or not \
                    profile_dict["instances"][instance]['Bastion']:
                ip_for_connection = profile_dict["instances"][instance]['Ip_public']
            else:
                ip_for_connection = instance

            if profile_dict["instances"][instance].get('Platform', False) == 'windows':
                if not profile_dict["instances"][instance]['Con_username']:
                    con_username = "Administrator"

            connection_command = f"{connection_command} {ip_for_connection}"

            if profile_dict["instances"][instance]['Bastion'] \
                    and not profile_dict["instances"][instance]['instance_use_ip_public'] \
                    or profile_dict["instances"][instance]['Instance_use_Bastion']:

                if profile_dict['instances'][instance]['Bastion_Con_username']:
                    bastion_connection_command = f"{profile_dict['instances'][instance]['Bastion_Con_username']}@" \
                                                 f"{profile_dict['instances'][instance]['Bastion']}"
                else:
                    bastion_connection_command = f"{profile_dict['instances'][instance]['Bastion']}"

                if profile_dict['instances'][instance]['Bastion_Con_port'] and \
                        profile_dict['instances'][instance]['Bastion_Con_port'] != 22:
                    bastion_connection_command = f"{bastion_connection_command}:" \
                                                 f"{profile_dict['instances'][instance]['Bastion_Con_port']}"

                connection_command = f"{connection_command} -J {bastion_connection_command}"

                if not profile_dict["instances"][instance]['Con_username'] and \
                        profile_dict["instances"][instance].get('Platform', False) == 'windows':
                    connection_command = f"function random_unused_port {{ local port=$( echo " \
                                         f"$((2000 + ${{RANDOM}} % 65000))); (echo " \
                                         f">/dev/tcp/127.0.0.1/$port) &> /dev/null ; if [[ $? != 0 ]] ; then export " \
                                         f"RANDOM_PORT=$port; else random_unused_port ;fi }}; " \
                                         f"if [[ -n ${{RANDOM_PORT+x}} && -n \"$( ps aux | grep \"ssh -f\" " \
                                         f"| grep -v grep | awk \'{{print $2}}\' )\" ]]; " \
                                         f" then kill -9 $( ps aux | grep \"ssh -f\" | grep -v grep " \
                                         f"| awk \'{{print $2}}\' ) ; else random_unused_port; fi ;ssh -f -o " \
                                         f"ExitOnForwardFailure=yes -L ${{RANDOM_PORT}}:{ip_for_connection}:" \
                                         f"{profile_dict['instances'][instance].get('con_port_windows', 3389)} " \
                                         f"{bastion_connection_command} sleep 10 ; open " \
                                         f"'rdp://full%20address=s:127.0.0.1:'\"${{RANDOM_PORT}}\"'" \
                                         f"&audiomode=i:2&disable%20themes=i:0&screen%20mode%20id=i:1&use%20multimon" \
                                         f":i:0&username:s:{con_username}" \
                                         f"&desktopwidth=i:1024&desktopheight=i:768'"
            elif profile_dict["instances"][instance].get('Platform', False) == 'windows':
                con_username = profile_dict["instances"][instance]['Con_username']
                connection_command = f"open 'rdp://full%20address=s:{ip_for_connection}:" \
                                     f"{profile_dict['instances'][instance].get('con_port_windows', 3389)}" \
                                     f"&audiomode=i:2&disable%20themes=i:0&screen%20mode%20id=i:1&use%20multimon" \
                                     f":i:0&username:s:{con_username}" \
                                     f"&desktopwidth=i:1024&desktopheight=i:768'"

            if profile_dict["instances"][instance]['Password'][0] and profile_dict["instances"][instance].get(
                    'Platform', '') == 'windows':
                connection_command = f"echo \"\\nThe Windows password on record is:\\n" \
                                     f"{profile_dict['instances'][instance]['Password'][1].rstrip()}\\n\\n\" " \
                                     f"\n;echo -n '{profile_dict['instances'][instance]['Password'][1].rstrip()}' "\
                                     f"| pbcopy; echo \"\\nIt has been sent to your clipboard for easy pasting\\n\\n\""\
                                     f";{connection_command}"

            elif profile_dict["instances"][instance].get('Platform', '') == 'windows':
                connection_command = f'echo \"\\nThe Windows password could not be decrypted...\\n' \
                                     f"The only hint we have is:{connection_command}\\n\\n\";" \
                                     f"\n{str(profile_dict['instances'][instance]['Password'][1])}"

            if profile_dict["instances"][instance].get('Platform', '') != 'windows':
                connection_command = f"{connection_command} {script_config['Local']['SSH_base_string']}"

                if profile_dict["instances"][instance]['Con_username']:
                    connection_command = f"{connection_command} -l "\
                                         f"{profile_dict['instances'][instance]['Con_username']}"

                if profile_dict["instances"][instance]['Con_port']:
                    connection_command = f"{connection_command} -p {profile_dict['instances'][instance]['Con_port']}"

                if profile_dict["instances"][instance]['SSH_key'] and \
                        profile_dict["instances"][instance]['use_shared_key']:
                    connection_command = f"{connection_command} -i {script_config['Local'].get('ssh_keys_path', '.')}" \
                                         f"/{profile_dict['instances'][instance]['SSH_key']}"

                if profile_dict["instances"][instance]['Login_command']:
                    connection_command = f"{connection_command} -t " \
                                         f"{profile_dict['instances'][instance]['Login_command']}"

            if profile_dict["instances"][instance]['Dynamic_profile_parent_name']:
                dynamic_profile_parent_name = profile_dict["instances"][instance]['Dynamic_profile_parent_name']
            else:
                dynamic_profile_parent_name = 'Default'

            profile = {"Name": profile_dict["instances"][instance]['Name'],
                       "Guid": f"{profile_dict['instance_source']}-{str(profile_dict['instances'][instance]['Id'])}",
                       "Badge Text": f"{badgeme(instance, profile_dict['instances'][instance])}",
                       "Tags": tags,
                       "Dynamic Profile Parent Name": dynamic_profile_parent_name,
                       "Custom Command": "Yes",
                       "Initial Text": connection_command
                       }

            profiles.append(profile)

        profiles = {"Profiles": profiles}
        with open(
                os.path.expanduser(
                    os.path.join(
                        CP_OutputDir,
                        f".{profile_dict['instance_source']}"
                        )
                ),
                'wt'
        ) as handle:
            handle.write(json.dumps(profiles, sort_keys=True, indent=4, separators=(',', ': ')))
        head_tail = os.path.split(handle.name)
        rename_target = head_tail[1][1:]
        os.rename(handle.name, os.path.join(head_tail[0], rename_target))


def update_statics(cp_output_dir, us_script_config):
    profiles = []
    with open(os.path.expanduser(os.path.join(cp_output_dir, ".statics")), "wt") as app_static_profile_handle:
        path_to_static_profiles = os.path.expanduser(us_script_config["Local"]['Static_profiles'])

        for root, _, files in os.walk(path_to_static_profiles, topdown=False):
            for name in files:
                if name == '.DS_Store':
                    continue
                print(f'Working on static profile: {name}')
                static_profile_handle = open(os.path.join(root, name))
                profiles.append(json.load(static_profile_handle))

        profiles = {"Profiles": profiles}
        app_static_profile_handle.write(json.dumps(profiles, sort_keys=True, indent=4, separators=(',', ': ')))
    shutil.move(app_static_profile_handle.name, os.path.expanduser(os.path.join(cp_output_dir, "statics")))


def docker_contexts_creator(dict_list):
    current_contexts = subprocess.run(
        ["docker", "context", "ls", "-q"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for profile_dict in dict_list:
        for instance in profile_dict['instances']:
            if profile_dict["instances"][instance]['docker_context']:
                context_name = f"{profile_dict['instances'][instance]['Name']}-{instance}"
                raw_iterm_tags = str(profile_dict['instances'][instance]['iterm_tags']).strip('[]')
                if profile_dict["instances"][instance]['Name'] not in current_contexts.stdout.decode('utf-8'):
                    print(f"Creating on Docker context for {context_name}")
                    try:
                        subprocess.run(
                            [
                                "docker",
                                "context",
                                "create",
                                context_name,
                                "--docker",
                                f"host=ssh://{context_name}",
                                "--description",
                                raw_iterm_tags
                            ],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                    except subprocess.CalledProcessError as err:
                        print('ERROR: There was en problem when creating the Docker context.\n', err)
                else:
                    print(f"Updating on Docker context for {context_name}")
                    try:
                        subprocess.run(
                            [
                                "docker",
                                "context",
                                "update",
                                context_name,
                                "--description",
                                raw_iterm_tags
                            ],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                    except subprocess.CalledProcessError as err:
                        print('ERROR: There was en problem when updating the Docker context.\n', err)


def update_ssh_config(dict_list):
    ssh_conf_file = empty_ssh_config_file()
    for profile_dict in dict_list:
        for instance in profile_dict['instances']:
            name = f"{profile_dict['instances'][instance]['Name']}-{instance}",
            ssh_conf_file.add(
                name,
                Hostname=instance,
                Port=profile_dict["instances"][instance]['Con_port'],
                User=profile_dict["instances"][instance]['Con_username'],
                ProxyJump=profile_dict["instances"][instance]['Bastion']
            )
            if not profile_dict["instances"][instance]['Con_username']:
                ssh_conf_file.unset(name, "user")
            if not profile_dict["instances"][instance]['Bastion']:
                ssh_conf_file.unset(name, "proxyjump")
    ssh_conf_file.write(CP_SSH_Config)


def aws_profiles_from_config_file(script_config_f, instance_counter_f, cloud_instances_obj_list_f):
    for profile in script_config_f['AWS']['profiles']:
        print(f"Working on {profile['name']}")
        if isinstance(profile.get("role_arns", False), dict):
            processes = []
            for role_arn_s in profile["role_arns"]:
                aws_p = mp.Process(
                    target=get_ec2_instances,
                    args=(
                        profile,
                        role_arn_s,
                        instance_counter_f,
                        script_config_f,
                        cloud_instances_obj_list_f
                    )
                )
                aws_p.start()
                processes.append(aws_p)

            for process in processes:
                process.join()

        else:
            get_ec2_instances(
                profile,
                instance_counter_f,
                script_config_f,
                cloud_instances_obj_list_f
            )


def aws_profiles_from_awscli_config(aws_script_config):
    if os.path.exists(os.path.expanduser(aws_script_config['AWS']['aws_credentials_file'])):
        config.read(os.path.expanduser(aws_script_config['AWS']['aws_credentials_file']))
        for i in config.sections():
            if i not in aws_script_config['AWS']['exclude_accounts']:
                print(f'Working on AWS profile from credentials file: {i}')
                get_ec2_instances(profile=i,
                                  ec2_instance_counter=instance_counter,
                                  ec2_script_config=aws_script_config
                                  )


def do_worker(do_script_config, do_instance_counter, do_cloud_instances_obj_list):
    for profile in do_script_config['DO']['profiles']:
        print(f"Working on {profile['name']}")
        get_do_instances(profile, do_instance_counter, do_script_config, do_cloud_instances_obj_list)


# Updates the /etc/hosts file with the EC2 private addresses
# /etc/hosts must include the list of EC2 instances between two lines: the first contains '# AWS EC2' 
# and the last a single # character.
def update_hosts(instances):
    with open('/etc/hosts') as handle:
        lines = handle.read().splitlines()
    state = False

    with open('/etc/hosts', 'wt')as hout:

        start_delimiter = "# AWS EC2"
        end_delimiter = "#"

        for line in lines:
            if line == start_delimiter:
                state = True
                continue
            if state and line == end_delimiter:
                state = False
                continue
            if not state:
                hout.write(line + "\n")

        hout.write(start_delimiter + "\n")
        for ip in instances:
            instance = instances[ip]
            name = instance['name']
            hout.write(ip + "\t" + name + "\n")

        hout.write(end_delimiter + "\n")


# MAIN
if __name__ == '__main__':
    with open("marker.tmp", "w") as file:
        file.write("mark")

    with mp.Manager() as manager:
        instance_counter: Dict[Any, Any] = manager.dict()
        cloud_instances_obj_list = manager.list()

        # instance_counter = {}
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # From repo
        with open(os.path.join(script_dir, 'config.yaml')) as conf_file:
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

        # From user home directory
        script_config = {}
        script_config_user = {}
        if os.path.isfile(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")):
            print("Found conf file in place")
            with open(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")) as conf_file:
                script_config_user = yaml.full_load(conf_file)
        else:
            if not os.path.isdir(os.path.expanduser("~/.iTerm-cloud-profile-generator/")):
                os.makedirs(os.path.expanduser("~/.iTerm-cloud-profile-generator/"))
            shutil.copy2(os.path.join(script_dir, 'config.yaml'),
                         os.path.expanduser("~/.iTerm-cloud-profile-generator/"))
            print(f"Copy default config to home dir {os.path.expanduser('~/.iTerm-cloud-profile-generator/')}")

        for key in script_config_repo:
            script_config[key] = {**script_config_repo.get(key, {}), **script_config_user.get(key, {})}

        username = getpass.getuser()
        config = configparser.ConfigParser()

        p_list = []
        # Static profiles iterator
        p = mp.Process(
            name="update_statics",
            target=update_statics,
            args=(CP_OutputDir, script_config)
        )
        p.start()
        p_list.append(p)

        # AWS profiles iterator
        if script_config['AWS'].get('profiles', False):
            # aws_profiles_from_config_file(script_config)
            p = mp.Process(
                name="aws_profiles_from_config_file",
                target=aws_profiles_from_config_file,
                args=(
                    script_config,
                    instance_counter,
                    cloud_instances_obj_list
                )
            )
            p.start()
            p_list.append(p)

        # AWS profiles iterator from config file
        if script_config['AWS'].get('use_awscli_profiles', False):
            p = mp.Process(
                target=aws_profiles_from_awscli_config,
                args=(
                    script_config,
                    instance_counter,
                    cloud_instances_obj_list
                )
            )
            p.start()
            p_list.append(p)

        # DO profiles iterator
        if script_config['DO'].get('profiles', False):
            p = mp.Process(target=do_worker, args=(script_config, instance_counter, cloud_instances_obj_list))
            p.start()
            p_list.append(p)

        for p in p_list:
            p.join()

        if platform.system() == 'Windows' or os.environ.get('CP_Windows', False):
            update_moba(cloud_instances_obj_list)
        else:
            update_term(cloud_instances_obj_list)
            # ssh_config
            if script_config['Local'].get('SSH_Config_create'):
                User_SSH_Config = os.path.expanduser("~/.ssh/config")
                CP_SSH_Config = os.path.expanduser("~/.ssh/cloud-profiler")
                with open(User_SSH_Config) as f:
                    if f"Include ~/.ssh/cloud-profiler" in f.read():
                        print(
                            "Found ssh_config include directive for CP in user's ssh config file, so leaving it as is.")
                    else:
                        print("Did not find include directive  for CP in user's ssh config file, so adding it.")
                        line_prepender(User_SSH_Config, "Include ~/.ssh/cloud-profiler")
                update_ssh_config(cloud_instances_obj_list)
            if script_config['Local'].get('docker_contexts_create'):
                docker_contexts_creator(cloud_instances_obj_list)

        if os.path.exists('marker.tmp'):
            os.remove("marker.tmp")
        jcounter = json.dumps(instance_counter.copy(), sort_keys=True, indent=4, separators=(',', ': '))
        jcounter_tot = sum(instance_counter.values())
        print(
            f"\nCreated profiles {jcounter}\nTotal: {jcounter_tot}"
        )
        print(f"\nWe wish you calm clouds and a serene path...\n")
