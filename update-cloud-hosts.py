#!/usr/local/bin/python
# coding: UTF-8

import base64
import concurrent.futures
import configparser
import json
import multiprocessing as mp
import os
import platform
import shutil
import subprocess
from typing import Any, Dict, Union

import boto3
import digitalocean
import yaml
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from inputimeout import TimeoutOccurred, inputimeout
from sshconf import empty_ssh_config_file
import ntplib
import sys


class InstanceProfile:
    script_config = {}
    """This is an instance profile"""

    def __init__(self):

        self.name = ""
        self.group = ""
        self.index = 0
        self.dynamic_profile_parent = ""
        self.con_username = ""
        self.bastion_con_username = ""
        self.con_port = 22
        self.bastion_con_port = 22
        self.id = 0
        self.ssh_key = ""
        self.use_shared_key = False
        self.login_command = ""
        self.instance_use_bastion = False
        self.bastion = ""
        self.instance_use_ip_public = False
        self.ip_public = ""
        self.password = ""
        self.region = ""
        self.docker_context = False
        self.instance_source = ""
        self.instance_flat_sgs = ""
        self.instance_flat_tags = ""
        self._iterm_tags_fin = []
        self.iterm_tags = []
        self._badge = []
        self.platform = False
        self.tags = []
        self.con_port_windows = 3389
        self.instancetype = ""
        self.ip = ""

    @property
    def iterm_tags_fin(self):
        for tag in self.iterm_tags:
            if ',' in tag:
                for shard in tag.split(','):
                    if shard.strip():
                        self._iterm_tags_fin.append(shard)
            else:
                self._iterm_tags_fin.append(tag)
        return self._iterm_tags_fin

    @property
    def badge(self):
        badge_to_return = []
        _name = self.name.split('.')
        if len(_name) == 4:
            name_formatted = f"Machine name: {_name[3]}\n" \
                             f"Cloud provider: {_name[0]}\n" \
                             f"Cloud account: {_name[2]}\n" \
                             f"Account profile: {_name[1]}"
        else:
            name_formatted = f"Instance name: {_name[2]}" \
                             f"Cloud provider: {_name[0]}" \
                             f"Account profile: {_name[1]}"
        all_badge_toggles = self.script_config["Local"].get("Badge_info_to_display", None)
        if not all_badge_toggles:
            value_to_return = f"{name_formatted}" \
                              f"InstanceType: {self.instancetype}" \
                              f"Ip_public: {self.ip_public}" \
                              f"Main_IP: {self.ip}"
        else:
            instance_dict = vars(self)
            for [badge_to_see, toggle] in all_badge_toggles.items():
                if toggle or isinstance(toggle, list):
                    if badge_to_see == "Instance_key":
                        badge_to_return.append(f"Main_IP: {self.ip}")
                    if badge_to_see == "Name" and toggle == "Formatted":
                        badge_to_return.append(f"{name_formatted}")
                        continue
                    if badge_to_see and self.password[1] != "":
                        badge_to_return.append(f"{badge_to_see}: {self.password[1]}")
                    if badge_to_see \
                            and not badge_to_see == "password" \
                            and not badge_to_see == "Instance_key" \
                            and not badge_to_see == "Iterm_tags_prefixs":
                        badge_to_return.append(f"{badge_to_see}: {str(instance_dict[badge_to_see.lower()])}")
                    if isinstance(toggle, list) and len(toggle) != 0:
                        badge_to_return.append(q_tag_flat(self.iterm_tags, toggle))
                    if isinstance(toggle, list) and len(toggle) == 0:
                        badge_to_return = f"{self.iterm_tags}"
            value_to_return = '\n'.join(filter(lambda x: x != "", badge_to_return))
        return value_to_return


def line_prepender(filename, line):
    with open(filename, 'r+') as file_to_append_to:
        content = file_to_append_to.read()
        file_to_append_to.seek(0, 0)
        file_to_append_to.write(line.rstrip('\r\n') + '\n' + content)


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
    plaintext = cipher.decrypt(ciphertext, "unable to decrypt").decode('utf-8')
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
            setting_value = profile.get(setting, False)
            if not setting_value:
                setting_value = resolver_script_config[caller_type].get(setting, False)
                if not setting_value:
                    setting_value = resolver_script_config["Local"].get(setting, False)
    return setting_value


def get_do_tag_value(tags, q_tag, q_tag_value) -> Union[int, str]:
    for tag in tags:
        tag = tag.casefold()
        if ':' in tag and ('iterm' in tag or 'cloud_profiler' in tags):
            tag_key, tag_value = tag.split(':')
            if tag_key == q_tag.casefold():
                q_tag_value = tag_value.replace('-', '.').replace('_', ' ')
                break
    return q_tag_value


def get_tag_value(tags, q_tag, sg=None, q_tag_value=False) -> Union[bool, int, str]:
    for tag in tags:
        tag['Key'] = tag.get('Key', '').casefold()
        if 'iterm_' in tag.get('Key', ''):
            tag['Key'] = tag['Key'].rpartition('iterm_')[2]
        if 'cloud_profiler_' in tag.get('Key', ''):
            tag['Key'] = tag['Key'].rpartition('cloud_profiler_')[2]
        if q_tag == 'flat' and not sg:
            if not q_tag_value:
                q_tag_value = ''
            q_tag_value += tag['Key'] + ': ' + tag['Value'] + ","
        elif q_tag == 'flat' and sg == "sg":
            if not q_tag_value:
                q_tag_value = ''
            q_tag_value += tag['GroupName'] + ': ' + tag['GroupId'] + ","
        else:
            if q_tag.casefold() == tag['Key'].casefold():
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
                        tag['Key'] = tag.get('Key', '').casefold()
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

    do_instance_counter[instance_source] = 0
    do_manager = digitalocean.Manager(token=profile['token'])
    my_droplets = do_manager.get_all_droplets()

    for drop in my_droplets:
        machine = InstanceProfile()
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
        dynamic_profile_parent = setting_resolver('dynamic_profile_parent', drop, {}, "DO", False, profile,
                                                  do_script_config)
        public_ip = drop.ip_address

        machine.con_port = con_port
        machine.bastion_con_username = bastion_con_username
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
        machine.ip = ip
        machine.name = f"{instance_source}.{drop_name}"
        machine.group = drop_name
        machine.index = groups[drop.name]
        machine.dynamic_profile_parent = dynamic_profile_parent
        machine.iterm_tags = iterm_tags
        machine.instancetype = drop.size['slug']
        machine.con_username = con_username
        machine.bastion_con_port = bastion_con_port
        machine.id = drop.id
        machine.ssh_key = ssh_key
        machine.use_shared_key = use_shared_key
        machine.login_command = login_command
        machine.instance_use_bastion = instance_use_bastion
        machine.bastion = bastion
        machine.instance_use_ip_public = instance_use_ip_public
        machine.ip_public = public_ip
        machine.password = password
        machine.region = drop.region['name']
        machine.docker_contexts_create = docker_context
        machine.instance_source = instance_source
        machine.provider_long = "DigitalOcean"
        machine.provider_short = "DO"

        print(
            f'instance_source: {machine.instance_source}. {machine.name}\tassociated bastion: "{str(machine.bastion)}"'
        )

        do_cloud_instances_obj_list.append(machine)


def fetch_ec2_instance(
        instance,
        client,
        groups,
        instance_source,
        vpc_data_all,
        profile,
        fetch_script_config
):
    instance_flat_tags = ''
    iterm_tags = []
    password = [False, ""]
    machine = InstanceProfile()

    docker_context = setting_resolver('docker_context', instance, vpc_data_all, 'AWS', False, profile,
                                      fetch_script_config)
    instance_use_bastion = setting_resolver('instance_use_bastion', instance, vpc_data_all, 'AWS', False, profile,
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
    dynamic_profile_parent = setting_resolver('dynamic_profile_parent', instance, vpc_data_all, 'AWS', False,
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
        pass_response = client.get_password_data(
            InstanceId=instance['InstanceId'],
        )
        data = base64.b64decode(pass_response.get('PasswordData', "U29ycnkgbm8ga2V5IHVzZWQgdG8gY3JlYXRlIFZNPw=="))
        password = decrypt(data, os.path.join(fetch_script_config["Local"].get('SSH_keys_path', '.'), ssh_key))

    machine.name = f"{instance_source}.{name}"
    machine.index = groups[name]
    machine.group = name
    machine.bastion = bastion
    machine.vpc = instance.get('VpcId', ""),
    machine.instance_use_ip_public = instance_use_ip_public
    machine.instance_use_bastion = instance_use_bastion
    machine.ip_public = public_ip
    machine.dynamic_profile_parent = dynamic_profile_parent
    machine.iterm_tags = iterm_tags_fin
    machine.instancetype = instance['InstanceType']
    machine.con_username = con_username
    machine.bastion_con_username = bastion_con_username
    machine.con_port = con_port
    machine.bastion_con_port = bastion_con_port
    machine.id = instance['InstanceId']
    machine.ssh_key = ssh_key
    machine.use_shared_key = use_shared_key
    machine.login_command = login_command
    machine.platform = instance.get('Platform', '')
    machine.password = password
    machine.region = instance['Placement']['AvailabilityZone'][:-1]
    machine.docker_context = docker_context
    machine.instance_source = instance_source
    machine.ip = ip
    machine.provider_long = "Amazon_Web_Services"
    machine.provider_short = "AWS"

    return machine


def fetch_ec2_region(
        region,
        groups,
        instance_source,
        credentials=None,
        profile=None,
        fetch_script_config=None,
        ec2_cloud_instances_obj_list=None
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
        }]
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
                        instance_source,
                        vpc_data_all,
                        profile,
                        fetch_script_config
                    )
                    results_value = future.result()
                    print(
                        f"{results_value.instance_source}: {results_value.name}\t"
                        f"associated bastion: {results_value.bastion}"
                    )
                    ec2_cloud_instances_obj_list.append(results_value)
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
    credentials = False
    assumed_role_object = None

    if isinstance(profile, dict):
        instance_source = "aws." + profile['name']
        profile_name = profile['name']
        boto3.setup_default_session(aws_access_key_id=profile['aws_access_key_id'],
                                    aws_secret_access_key=profile['aws_secret_access_key'],
                                    region_name="eu-central-1")
    else:
        instance_source = "aws." + profile
        boto3.setup_default_session(profile_name=profile, region_name="eu-central-1")
        profile_name = profile

    if ec2_role_arn:
        instance_source = f"{instance_source}.{ec2_role_arn}"
        role_session_name = f"{os.path.basename(__file__).rpartition('.')[0]}." \
                            f"cloud_profiler@{platform.uname()[1]}"
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
            groups,
            instance_source,
            credentials,
            profile,
            ec2_script_config,
            ec2_cloud_instances_obj_list
        )


def update_moba(obj_list):
    bookmark_counter = 1

    profiles = "[Bookmarks]\nSubRep=\nImgNum=42"
    for machine in obj_list:

        instance_counter[machine.instance_source] += 1

        profiles += f"""\n[Bookmarks_{bookmark_counter}]
                    SubRep={machine.provider_short}\\{machine.instance_source}\\{machine.region}\nImgNum=41\n"""

        short_name = machine.name.rpartition('.')[2]

        connection_command = f"{short_name}= "

        tags = ["Account: " + machine.instance_source, str(machine.id)]
        for tag in machine.iterm_tags:
            tags.append(tag)

        if "Sorry" in machine.ip:
            connection_command = "echo"
            ip_for_connection = machine.ip
        elif machine.instance_use_ip_public or not machine.bastion:
            ip_for_connection = machine.ip_public
        else:
            ip_for_connection = machine.ip

        if machine.con_username:
            con_username = machine.con_username
        else:
            con_username = '<default>'

        if machine.platform == 'windows':
            if not machine.con_username:
                con_username = "Administrator"
            connection_type = "#91#4%"
        else:
            connection_type = "#109#0%"

        if (isinstance(machine.bastion, str) and not machine.instance_use_ip_public) \
                or machine.instance_use_bastion:

            bastion_for_profile = machine.bastion
        else:
            bastion_for_profile = ''

        if machine.ssh_key and machine.use_shared_key:
            shard_key_path = os.path.join(connection_command, os.path.expanduser(
                script_config["Local"].get('ssh_keys_path', '.')), machine.ssh_key)
        else:
            shard_key_path = ''
        tags = ','.join(tags)
        if machine.bastion_con_port != 22:
            bastion_port = machine.bastion_con_port
        else:
            bastion_port = ''
        if machine.bastion_con_username:
            bastion_user = machine.con_username
        else:
            bastion_user = ''
        if machine.login_command:
            login_command = machine.login_command.replace('"', "").replace("|", "__PIPE__").replace("#", "__DIEZE__")
        else:
            login_command = ''
        profile = (
            f"\n{short_name}= {connection_type}{ip_for_connection}%{machine.con_port}%"
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


def update_term(obj_list):
    con_username = None
    profiles = []

    p_region_list = {}
    for obj in obj_list:

        if obj.provider_short not in p_region_list:
            p_region_list[obj.provider_short] = []
        p_region_list[obj.provider_short].append(obj)

    for cloud_provider, machines in p_region_list.items():
        for machine in machines:
            instance_counter[machine.instance_source] += 1
            connection_command = f"{script_config['Local'].get('SSH_command', 'ssh')}"
            machine.tags = [f"Account: {machine.instance_source}, {machine.ip}"]
            for tag in machine.iterm_tags:
                machine.tags.append(tag)

            if "Sorry" in machine.ip:
                connection_command = "echo"
                ip_for_connection = machine.ip
            elif machine.instance_use_ip_public or not machine.bastion:
                ip_for_connection = machine.ip_public
            else:
                ip_for_connection = machine.ip

            if machine.platform == 'windows':
                if not machine.con_username:
                    con_username = "Administrator"

            connection_command = f"{connection_command} {ip_for_connection}"

            if machine.bastion \
                    and not machine.instance_use_ip_public \
                    or machine.instance_use_bastion:

                if machine.bastion_con_username:
                    bastion_connection_command = f"{machine.bastion_con_username}@{machine.bastion}"
                else:
                    bastion_connection_command = f"{machine.bastion}"

                if machine.bastion_con_port and \
                        machine.bastion_con_port != 22:
                    bastion_connection_command = f"{bastion_connection_command}:{machine.bastion_con_port}"

                connection_command = f"{connection_command} -J {bastion_connection_command}"

                if not machine.con_username and machine.platform == 'windows':
                    connection_command = \
                         "function random_unused_port() { LOW_BOUND=49152 ; RANGE=16384 ; " \
                         "while true; do RANDOM_PORT=$[$LOW_BOUND + ($RANDOM % $RANGE)]; " \
                         "(echo '' >/dev/tcp/127.0.0.1/${RANDOM_PORT}) &>/dev/null;" \
                         "if [ $? -ne 0 ]; then echo $RANDOM_PORT ; break ; fi; done };" \
                         f"if [[ -n ${{RANDOM_PORT+x}} && -n \"$( ps aux | grep \"ssh -f\" " \
                         f"| grep -v grep | awk \'{{print $2}}\' )\" ]]; " \
                         f" then kill -9 $( ps aux | grep 'ssh -f' | grep -v grep " \
                         f"| awk \'{{print $2}}\' ) ; else random_unused_port; fi ;ssh -f -o " \
                         f"ExitOnForwardFailure=yes -L ${{RANDOM_PORT}}:{ip_for_connection}:" \
                         f"{machine.con_port_windows} " \
                         f"{bastion_connection_command} sleep 10 ; open " \
                         f"'rdp://full%20address=s:127.0.0.1:'\"${{RANDOM_PORT}}\"'" \
                         f"&audiomode=i:2&disable%20themes=i:0&screen%20mode%20id=i:1&use%20multimon" \
                         f":i:0&username:s:{con_username}" \
                         f"&desktopwidth=i:1024&desktopheight=i:768'"
            elif machine.platform == 'windows':
                con_username = machine.con_username
                connection_command = f"open 'rdp://full%20address=s:{ip_for_connection}:" \
                                     f"{machine.con_port_windows}" \
                                     f"&audiomode=i:2&disable%20themes=i:0&screen%20mode%20id=i:1&use%20multimon" \
                                     f":i:0&username:s:{con_username}" \
                                     f"&desktopwidth=i:1024&desktopheight=i:768'"

            if machine.password[0] and machine.platform == 'windows':
                connection_command = f"#The Windows password on record is:\n" \
                                     f"#\"{machine.password[1].rstrip()}\"\n\n" \
                                     f"echo -n '{machine.password[1].rstrip()}'|pbcopy\n\n" \
                                     f"#The password has been copied to your clipboard for easy pasting.\n" \
                                     f"{connection_command}"

            elif machine.platform == 'windows':
                connection_command = f'echo \"\\nThe Windows password could not be decrypted...\\n' \
                                     f"The only hint we have is:{connection_command}\\n\\n\";" \
                                     f"\n{str(machine.password[1])}"

            if machine.platform != 'windows':
                connection_command = f"{connection_command} {script_config['Local']['SSH_base_string']}"

                if machine.con_username:
                    connection_command = f"{connection_command} -l {machine.con_username}"

                if machine.con_port:
                    connection_command = f"{connection_command} -p {machine.con_port}"

                if machine.ssh_key and machine.use_shared_key:
                    connection_command = f"{connection_command} -i {script_config['Local'].get('SSH_keys_path', '.')}" \
                                         f"/{machine.ssh_key}"

                if machine.login_command:
                    connection_command = f"{connection_command} -t {machine.login_command}"

            if machine.dynamic_profile_parent:
                profile_dynamic_profile_parent = machine.dynamic_profile_parent
            else:
                profile_dynamic_profile_parent = 'Default'

            profile = {"Name": machine.name,
                       "Guid": f"{machine.instance_source}-{str(machine.id)}",
                       "Badge Text": machine.badge,
                       "Tags": machine.tags,
                       "Dynamic Profile Parent Name": profile_dynamic_profile_parent,
                       "Custom Command": "Yes",
                       "Initial Text": connection_command
                       }

            profiles.append(profile)

        p_profiles = {"Profiles": profiles}
        with open(
                os.path.expanduser(
                    os.path.join(
                        CP_OutputDir,
                        f".CP-{cloud_provider}-{VERSION}.json"
                    )
                ),
                'wt'
        ) as handle:
            handle.write(json.dumps(p_profiles, sort_keys=True, indent=4, separators=(',', ': ')))
        head_tail = os.path.split(handle.name)
        rename_target = head_tail[1][1:]
        os.rename(handle.name, os.path.join(head_tail[0], rename_target))
        profiles = []


def update_statics(cp_output_dir, us_script_config, _version):
    profiles = []
    with open(os.path.expanduser(os.path.join(cp_output_dir, f".CP-statics-{_version}.json")), "wt") \
            as app_static_profile_handle:
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
    shutil.move(
        app_static_profile_handle.name, os.path.expanduser(
            os.path.join(
                cp_output_dir, f"CP-statics-{_version}.json")
        )
    )


def docker_contexts_creator(dict_list):
    current_contexts = subprocess.run(
        ["docker", "context", "ls", "-q"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for machine in dict_list:
        if machine.docker_context:
            context_name = f"{machine.name}-{machine.ip}-{machine.id}"
            raw_iterm_tags = str(machine.iterm_tags)
            if machine.name not in current_contexts.stdout.decode('utf-8'):
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
                    print('ERROR: There was en problem when updating the Docker context.\n', err)


def update_ssh_config(dict_list):
    ssh_conf_file = empty_ssh_config_file()
    for machine in dict_list:
        name = f"{machine.name}-{machine.ip}-{machine.id}"
        ssh_conf_file.add(
            name,
            Hostname=machine.ip,
            Port=machine.con_port,
            User=machine.con_username,
            ProxyJump=machine.bastion
        )
        if not machine.con_username:
            ssh_conf_file.unset(name, "user")
        if not ((isinstance(machine.bastion, str) and not machine.instance_use_ip_public)
                or machine.instance_use_bastion):
            ssh_conf_file.unset(name, "proxyjump")
        print(f"Added {name} to SSH config list.")
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
            role_arn_s = False
            get_ec2_instances(
                profile,
                role_arn_s,
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


# MAIN
if __name__ == '__main__':
    VERSION = "v4.4.1"
    c = ntplib.NTPClient()
    time_response = c.request('time.google.com', version=3)
    max_api_drift = 15 * 60
    if time_response.offset > max_api_drift:
        print("Cloud-Profiler - The current system time is more then 15 minutes offset from the world. "
              "Fix this and try again.")
        sys.exit(42)

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

        print(platform.system())
        if os.environ.get('CP_OutputDir', False):
            CP_OutputDir = os.environ['CP_OutputDir']
        elif platform.system() == 'Windows' or os.environ.get('CP_Windows', False):
            CP_OutputDir = "~/Documents/Cloud-profiler/DynamicProfiles"
        elif platform.system() == 'Darwin':
            CP_OutputDir = "~/Library/Application Support/iTerm2/DynamicProfiles/"
        else:
            CP_OutputDir = "~/DynamicProfiles/"
        print(f"CP_OutputDir to be used: {CP_OutputDir}")

        if not os.path.isdir(os.path.expanduser(CP_OutputDir)):
            os.makedirs(os.path.expanduser(CP_OutputDir))

        # From user home directory
        script_config = {}
        script_config_user = {}
        if os.path.isfile(os.path.expanduser("~/.iTerm-cloud-profile-generator/config.yaml")):
            print("Cloud-profiler - Found conf file in place")
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

        InstanceProfile.script_config = script_config

        config = configparser.ConfigParser()

        # Clean legacy
        if script_config["Local"].get("CNC", True):
            for entry in os.scandir(os.path.expanduser(CP_OutputDir)):
                if not entry.is_dir(follow_symlinks=False):
                    if "CP" not in entry.name or \
                            VERSION not in entry.name:
                        os.remove(entry.path)

        p_list = []
        
        # Static profiles iterator
        if platform.system() == 'Windows' or os.environ.get('CP_Windows', False) == 'True' or \
                os.environ.get('WSL', False) == 'True':
            print("Cloud-profiler - Skipping creating \"static profiles\", as this seems to be a windows system.")
        else:
            p = mp.Process(
                name="update_statics",
                target=update_statics,
                args=(CP_OutputDir, script_config, VERSION,)
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

        """Wait for all processes (cloud providers) to finish before moving on"""
        for p in p_list:
            p.join()

        if platform.system() == 'Windows' or os.environ.get('CP_Windows', False) == 'True' or \
                os.environ.get('WSL', False) == 'True':
            update_moba(cloud_instances_obj_list)
        else:
            update_term(cloud_instances_obj_list)
        # ssh_config
        if platform.system() != 'Windows':
            if script_config['Local'].get('SSH_Config_create'):
                print("Cloud-profiler - SSH_Config_create is set, so will create config.")
                User_SSH_Config = os.path.expanduser("~/.ssh/config")
                CP_SSH_Config = os.path.expanduser("~/.ssh/cloud-profiler")
                with open(User_SSH_Config) as f:
                    if f"Include ~/.ssh/cloud-profiler" in f.read():
                        print(
                            "Cloud-profiler - Found ssh_config include directive for CP in user's ssh config file, "
                            "so leaving it as is.")
                    else:
                        print('Cloud-profiler - Did not find include directive  for CP in user\'s ssh config file, '
                              'so adding it.')
                        line_prepender(User_SSH_Config, "Include ~/.ssh/cloud-profiler")
                update_ssh_config(list(cloud_instances_obj_list))
            if script_config['Local'].get('Docker_contexts_create'):
                docker_contexts_creator(list(cloud_instances_obj_list))

        if os.path.exists('marker.tmp'):
            os.remove("marker.tmp")
        jcounter = json.dumps(instance_counter.copy(), sort_keys=True, indent=4, separators=(',', ': '))
        jcounter_tot = sum(instance_counter.values())
        print(
            f"\nCreated profiles {jcounter}\nTotal: {jcounter_tot}"
        )
        print(f"\nWe wish you calm clouds and a serene path...\n")
