#!/usr/local/bin/python
# coding: UTF-8

import urllib3.exceptions
import base64
import concurrent.futures
import configparser
import getpass
import json
import multiprocessing as mp
import multiprocessing.dummy as th
import os
import platform
import shutil
import socket
import subprocess
from typing import Any, Dict, Union

import boto3
import digitalocean
import requests
import yaml
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from inputimeout import TimeoutOccurred, inputimeout
import re
from sshconf import empty_ssh_config_file
from pyVmomi import vim
from pyVim import connect
import ctypes.wintypes
import random
from linode_api4 import LinodeClient

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
    if caller_type == 'DO' or caller_type == 'Linode':
        setting_value = get_do_and_linode_tag_value(instance.tags, setting, setting_value)
    if caller_type == 'ESX':
        setting_value = get_esx_tag_value(instance.config.annotation, setting, setting_value)
    if not setting_value:
        if caller_type == 'AWS' and instance['State']['Name'] != "terminated":
            setting_value = vpc_data(instance['VpcId'], setting, vpc_data_all)
        if caller_type == 'DO':
            pass
        if not setting_value and not setting_value == "":
            setting_value = profile.get(setting, False)
            if not setting_value and not setting_value == "":
                setting_value = profile.get(setting.casefold(), False)
                if not setting_value and not setting_value == "":
                    setting_value = resolver_script_config[caller_type].get(setting, False)
                    if not setting_value and not setting_value == "":
                        setting_value = resolver_script_config["Local"].get(setting, False)
    return setting_value


def get_do_and_linode_tag_value(tags, q_tag, q_tag_value) -> Union[int, str]:
    for tag in tags:
        tag = tag.casefold()
        if ':' in tag and ('iterm' in tag or 'cloud_profiler' in tag):
            tag_key, tag_value = tag.split(':')
            if q_tag.casefold() in tag_key:
                q_tag_value = tag_value.replace('-', '.').replace('_', ' ')
                break
    return q_tag_value


def get_esx_tag_value(tags, q_tag, q_tag_value) -> Union[int, str]:
    for tag in tags.split("\n"):
        tag = tag.casefold()
        if ':' in tag and ('iterm' in tag or 'cloud_profiler' in tag):
            tag_key, tag_value = re.split(':|: ', tag)
            if q_tag.casefold() in tag_key:
                q_tag_value = tag_value.strip()
                break
    return q_tag_value


def get_tag_value(tags, q_tag, sg=None, q_tag_value=False) -> Union[bool, int, str]:
    for tag in tags:
        tag['Key'] = tag.get('Key', '').casefold().replace('\t', '').replace('\n', '')
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


def get_linode_instances(profile, linode_instance_counter, linode_script_config, linode_cloud_instances_obj_list):
    instance_source = "Linode." + profile['name']
    linode_instance_counter[instance_source] = 0
    client = LinodeClient(profile['token'])
    lnodes = client.linode.instances()
    for lnode in lnodes:
        machine = InstanceProfile()
        if (linode_script_config['DO'].get('Skip_stopped', True)
            and linode_script_config['Local'].get('Skip_stopped', True)
            and profile.get('Skip_stopped', True)) \
                and lnode.status != 'running':
            continue

        l_password = [False, ""]
        iterm_tags = []
        docker_context = setting_resolver(
            'Docker_contexts_create', machine, {}, "Linode", False, profile, linode_script_config
        )
        instance_use_ip_public = setting_resolver(
            'instance_use_ip_public', machine, {}, "Linode", False, profile, linode_script_config
        )
        instance_use_bastion = setting_resolver(
            'Use_bastion', machine, {}, "Linode", False, profile, linode_script_config
        )
        or_host_name = setting_resolver(
            'Host_name', machine, {}, "Linode", False, profile, linode_script_config
        )
        bastion = setting_resolver(
            'Bastion', machine, {}, "Linode", False, profile, linode_script_config
        )
        con_username = setting_resolver(
            'Con_username', machine, {}, "Linode", False, profile, linode_script_config
        )
        bastion_con_username = setting_resolver(
            'Bastion_Con_username', machine, {}, "Linode", False, profile, linode_script_config
        )
        con_port = setting_resolver(
            'Con_port', machine, {}, "Linode", 22, profile, linode_script_config
        )
        bastion_con_port = setting_resolver(
            'Bastion_Con_port', machine, {}, "Linode", 22, profile, linode_script_config
        )
        ssh_key = setting_resolver(
            'SSH_key', machine, {}, "Linode", False, profile, linode_script_config
        )
        use_shared_key = setting_resolver(
            'use_shared_key', machine, {}, "Linode", False, profile, linode_script_config
        )
        login_command = setting_resolver(
            'Login_command', machine, {}, "Linode", False, profile, linode_script_config
        )
        dynamic_profile_parent = setting_resolver(
            'dynamic_profile_parent', machine, {}, "Linode", False, profile, linode_script_config
        )
        public_ip = lnode.ipv4[0]

        machine.con_port = con_port
        machine.bastion_con_username = bastion_con_username
        if or_host_name:
            linode_name = or_host_name
        else:
            linode_name = lnode.label

        if instance_use_ip_public:
            ip = lnode.ipv4[0]
        else:
            ip = "sorry"

        if lnode.tags:
            for tag in lnode.tags:
                if tag:
                    iterm_tags.append(tag)

        iterm_tags += f"ip: {ip}", f"Name: {lnode.label}"
        machine.ip = ip
        machine.name = f"{instance_source}.{linode_name}"
        machine.group = linode_name
        machine.dynamic_profile_parent = dynamic_profile_parent
        machine.iterm_tags = iterm_tags
        machine.instancetype = lnode.type.id
        machine.con_username = con_username
        machine.bastion_con_port = bastion_con_port
        machine.id = lnode.id
        machine.ssh_key = ssh_key
        machine.use_shared_key = use_shared_key
        machine.login_command = login_command
        machine.instance_use_bastion = instance_use_bastion
        machine.bastion = bastion
        machine.instance_use_ip_public = instance_use_ip_public
        machine.ip_public = public_ip
        machine.password = l_password
        machine.region = lnode.region.id
        machine.docker_contexts_create = docker_context
        machine.instance_source = instance_source
        machine.provider_long = "Linode"
        machine.provider_short = "Linode"

        print(
            f'instance_source: {machine.instance_source}. {machine.name}\tassociated bastion: "{str(machine.bastion)}"'
        )

        linode_cloud_instances_obj_list.append(machine)


def get_do_instances(profile, do_instance_counter, do_script_config, do_cloud_instances_obj_list):
    instance_source = f"DO.{profile['name']}"

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
            'instance_use_ip_public', drop, {}, "DO", False, profile, do_script_config
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

        if drop.tags:
            for tag in drop.tags:
                if tag:
                    iterm_tags.append(tag)

        iterm_tags += f"ip: {ip}", f"Name: {drop.name}"
        machine.ip = ip
        machine.name = f"{instance_source}.{drop_name}"
        machine.group = drop_name
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


def get_esx_instances(
        views,
        esx_script_config,
        profile,
        instance_source,
        esx_cloud_instances_obj_list
):
    for esx_vm in views:
        machine = InstanceProfile()
        if (esx_script_config['ESX'].get('Skip_stopped', True)
            and esx_script_config['Local'].get('Skip_stopped', True)
            and profile.get('Skip_stopped', True)) \
                and esx_vm.runtime.powerState != 'poweredOn':
            continue

        password = [False, ""]
        iterm_tags = []
        docker_context = setting_resolver(
            'Docker_contexts_create', esx_vm, {}, "ESX", False, profile, esx_script_config)
        instance_use_ip_public = setting_resolver(
            'instance_use_ip_public', esx_vm, {}, "ESX", False, profile, esx_script_config
        )
        instance_use_bastion = setting_resolver('Use_bastion', esx_vm, {}, "ESX", False, profile, esx_script_config)
        or_host_name = setting_resolver('Host_name', esx_vm, {}, "ESX", False, profile, esx_script_config)
        bastion = setting_resolver('Bastion', esx_vm, {}, "ESX", False, profile, esx_script_config)
        con_username = setting_resolver('Con_username', esx_vm, {}, "ESX", False, profile, esx_script_config)
        bastion_con_username = setting_resolver('Bastion_Con_username', esx_vm, {}, "ESX", False, profile,
                                                esx_script_config)
        con_port = setting_resolver('Con_port', esx_vm, {}, "ESX", 22, profile, esx_script_config)
        bastion_con_port = setting_resolver('Bastion_Con_port', esx_vm, {}, "ESX", 22, profile, esx_script_config)
        ssh_key = setting_resolver('SSH_key', esx_vm, {}, "ESX", False, profile, esx_script_config)
        use_shared_key = setting_resolver('use_shared_key', esx_vm, {}, "ESX", False, profile, esx_script_config)
        login_command = setting_resolver('Login_command', esx_vm, {}, "ESX", False, profile, esx_script_config)
        dynamic_profile_parent = setting_resolver('dynamic_profile_parent', esx_vm, {}, "ESX", False, profile,
                                                  esx_script_config)
        public_ip = "Sorry... \"public IPs\" as a concept are not yet supported"

        if (esx_vm.guest.toolsInstallType is not None and "MSI" in esx_vm.guest.toolsInstallType) or \
                'windows' in esx_vm.config.guestId:
            machine.platform = 'windows'
        machine.con_port = con_port
        machine.bastion_con_username = bastion_con_username
        if or_host_name:
            esx_vm_name = or_host_name
        else:
            esx_vm_name = esx_vm.name

        if instance_use_ip_public:
            ip = esx_vm.ip_address
        elif esx_vm.guest.ipAddress is not None:
            ip = esx_vm.guest.ipAddress
        else:
            ip = "Sorry, we could not get the IP for the VM (may be a vmware-tools issue?)"

        for tag in esx_vm.config.annotation.split("\n"):
            tag = tag.casefold()
            if ':' in tag and ('iterm' in tag or 'cloud_profiler' in tag):
                tag_key, tag_value = re.split(':|: ', tag)
                iterm_tags.append(tag_value.strip())

        iterm_tags += f"ip: {ip}", f"Name: {esx_vm.name}"
        machine.ip = ip
        machine.name = f"{instance_source}.{esx_vm_name}"
        machine.group = esx_vm_name
        machine.dynamic_profile_parent = dynamic_profile_parent
        machine.iterm_tags = iterm_tags
        machine.instancetype = esx_vm.summary.config.numCpu
        machine.con_username = con_username
        machine.bastion_con_port = bastion_con_port
        machine.id = esx_vm.summary.config.instanceUuid
        machine.ssh_key = ssh_key
        machine.use_shared_key = use_shared_key
        machine.login_command = login_command
        machine.instance_use_bastion = instance_use_bastion
        machine.bastion = bastion
        machine.instance_use_ip_public = instance_use_ip_public
        machine.ip_public = public_ip
        machine.password = password
        machine.region = "Root"
        # TODO: understand directory structure of the ESX and map?
        machine.docker_contexts_create = docker_context
        machine.instance_source = instance_source
        machine.provider_long = "DigitalOcean"
        machine.provider_short = "ESX"

        print(
            f'instance_source: {machine.instance_source}. {machine.name}\tassociated bastion: "{str(machine.bastion)}"'
        )

        esx_cloud_instances_obj_list.append(machine)


def get_esx_instances_list(
        profile,
        esx_instance_counter,
        esx_script_config,
        esx_cloud_instances_obj_list,
        disable_ssl_cert_validation
):
    instance_source = "ESX." + profile['name']

    esx_instance_counter[instance_source] = 0

    my_cluster = connect.SmartConnect(
        host=profile['address'],
        port=profile.get('port', 443),
        user=profile['user'],
        pwd=profile['password'],
        disableSslCertValidation=disable_ssl_cert_validation
    )
    content = my_cluster.content

    container = content.viewManager.CreateContainerView(
        content.rootFolder,
        [vim.VirtualMachine],
        True
    )
    esx_split = []
    for view in container.view:
        esx_split.append(view)

    def divide_chunks(var_to_chunk, n):
        for i in range(0, len(var_to_chunk), n):
            yield var_to_chunk[i:i + n]

    p_esx_list = []
    for view in list(divide_chunks(esx_split, 10)):
        split_p = th.Process(
            target=get_esx_instances,
            args=(
                view,
                esx_script_config,
                profile,
                instance_source,
                esx_cloud_instances_obj_list
            )
        )
        split_p.start()
        p_esx_list.append(split_p)

    for _ in p_esx_list:
        _.join()


def fetch_ec2_instance(
        instance,
        client,
        instance_source,
        vpc_data_all,
        profile,
        fetch_script_config
):
    instance_flat_tags = ''
    iterm_tags = []
    password = [False, ""]
    machine = InstanceProfile()

    if 'Tags' in instance:
        name = get_tag_value(instance['Tags'], "Name", False, instance['InstanceId'])
        instance_flat_tags = get_tag_value(instance['Tags'], 'flat')
    else:
        name = instance['InstanceId']

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

    if instance_use_ip_public and 'PublicIpAddress' in instance:
        ip = instance['PublicIpAddress']
    else:
        try:
            ip = instance['NetworkInterfaces'][0]['PrivateIpAddress']
        except IndexError:
            ip = r'No IP found at scan time ¯\_(ツ)_/¯, probably a terminated instance. (Sorry)#'

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

    machine.name = f"{instance_source}.{name}"
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
        instance_source,
        credentials=None,
        profile=None,
        fetch_script_config=None,
        ec2_cloud_instances_obj_list=None
) -> None:
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
                            f"{getpass.getuser().replace(' ', '_')}@{platform.uname()[1]}"
        if not checkinternetrequests(
                url="https://sts.amazonaws.com/",
                vanity=f"AWS STS endpoint for use with \"{profile_name}.{ec2_role_arn}",
                verify=True,
                terminate=False
        ):
            return
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
        if not checkinternetrequests(
                url="https://ec2.eu-central-1.amazonaws.com/",
                vanity=f"AWS EC2 API for use with \"{profile_name}\"",
                terminate=False
        ):
            return
        client = boto3.client('ec2')
    ec2_instance_counter[instance_source] = 0

    try:
        ec2_regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    except Exception as e:
        print(f'Was unable to retrieve information for "regions" in account "{profile_name}", so it was skipped.')
        print(f"The exception was:\n{e}")
        return

    from_config_region_filters = [
        *ec2_script_config['AWS'].get('exclude_regions', []),
        *profile.get('exclude_regions', [])
    ]
    print(f"{instance_source}: filtering out these regions: {from_config_region_filters}")
    ec2_regions_filtered = list(set(ec2_regions) - set(from_config_region_filters))

    p_region_list = []
    for region in ec2_regions_filtered:
        region_p = th.Process(
            target=fetch_ec2_region,
            args=(
                region,
                instance_source,
                credentials,
                profile,
                ec2_script_config,
                ec2_cloud_instances_obj_list
            )
        )
        region_p.start()
        p_region_list.append(region_p)

    for _ in p_region_list:
        _.join()


def update_moba(obj_list):
    profiles = "[Bookmarks]\nSubRep=\nImgNum=42"

    # update profile
    profiles += f"\n[Bookmarks_1]" \
                f"\nCP Update profiles {VERSION} =" \
                f";  logout#151#14%Default%%Interactive " \
                f"shell%__PTVIRG__[ -z ${{CP_Version+x}} ] " \
                f"&& CP_Version__EQUAL__'v7.1.0_Alanis_Jagged'__PTVIRG__[ -z ${{CP_Branch+x}} ] " \
                f"&& CP_Branch__EQUAL__'main'__PTVIRG__" \
                f"[ __DBLQUO__${{CP_Branch}}__DBLQUO__ __EQUAL____EQUAL__ __DBLQUO__develop__DBLQUO__ ] " \
                f"&& CP_Version__EQUAL__'edge'__PTVIRG__" \
                f"bash <(curl -s https://raw.githubusercontent.com/aviadra/Cloud-profiler/$CP_Branch/startup.sh)__" \
                f"PTVIRG__%%0#MobaFont%10%0%0%-1%15%248,248,242%40,42,54%153,153,153%0%-1%0%%xterm%-1%-1%_" \
                f"Std_Colors_0_%80%24%0%1%-1%<none>%12:2:0:" \
                f"curl -s https__DBLDOT__//raw.githubusercontent.com/aviadra/Cloud-profiler/main/startup.sh " \
                f"__PIIPE__ bash__PIPE__%0%0%-1#0# #-1"

    # update profile
    bookmark_counter = 2

    for machine in obj_list:
        instance_counter[machine.instance_source] += 1

        profiles += f"\n[Bookmarks_{bookmark_counter}]" \
                    f"\nSubRep={machine.provider_short}\\{machine.instance_source}\\{machine.region}\nImgNum=41\n"

        pcolors = "#MobaFont%10%0%0%-1%15%236,236,236%30,30,30""%180,180,192%0%-1%0%%%xterm%-1%-1%_Std_Colors_0_"
        if machine.dynamic_profile_parent:
            res = next(
                (
                    sub for sub in script_config['Local']['Moba']['colors']
                    if sub['name'].casefold() == machine.dynamic_profile_parent.casefold()
                ),
                None
            )
            pcolors = res.get('RGBs', pcolors).replace(" ", "")

        short_name = machine.name.rpartition('.')[2]

        connection_command = f"{short_name}= "

        tags = ["Account: " + machine.instance_source, str(machine.id)]
        for tag in machine.iterm_tags:
            tags.append(tag)

        if machine.ip is not None and "Sorry" in machine.ip:
            connection_command = "echo"
            ip_for_connection = machine.ip
        elif (machine.instance_use_ip_public or not machine.bastion) \
                and machine.instance_use_bastion:
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
            if machine.con_port == 22:
                machine.con_port = 3389
            connection_type = "#91#4%"
            bastion_for_profile = '%0%0'
            bastion_prefix = '%0%0%-1%%'
        else:
            connection_type = "#109#0%"
            bastion_for_profile = ''
            bastion_prefix = ''

        if (isinstance(machine.bastion, str) and not machine.instance_use_ip_public) \
                or machine.instance_use_bastion:
            bastion_for_profile = f"{bastion_prefix}{machine.bastion}"
        elif machine.platform == 'windows':
            machine.bastion_con_port = '-1'

        if machine.ssh_key and machine.use_shared_key:
            shard_key_path = os.path.join(connection_command, os.path.expanduser(
                script_config["Local"].get('ssh_keys_path', '.')), machine.ssh_key)
        else:
            shard_key_path = ''
        tags = ','.join(tags)
        if machine.bastion_con_username:
            bastion_user = machine.con_username
        else:
            bastion_user = ''
        if machine.login_command and not machine.platform == 'windows' and not machine.login_command == "null":
            login_command = machine.login_command.replace('"', "").replace("|", "__PIPE__").replace("#", "__DIEZE__")
        elif machine.platform == 'windows':
            login_command = '-1%-1'
        else:
            login_command = ''
        if not machine.platform == 'windows' and \
                script_config['Local'].get('Moba', {}).get('echo_ssh_command', {}).get('toggle', False) and \
                script_config['Local'].get('Moba', {}).get('echo_ssh_command', {}).get('assumed_shell', False):
            tags_formatted = tags.replace(",", "\\n")
            cosmetic_login_cmd = f"Cloud-profiler - What we know of this machine is:" \
                                 f"\\nProvider: {machine.provider_long}" \
                                 f"\\nIP: {machine.ip}" \
                                 f"\\n{tags_formatted}\\n"
            ip_providers = script_config['Local'].get('Moba', {}).get('echo_ssh_command', {}).get('what_is_my_ip', [])
            if script_config['Local'].get('Moba', {}).get('echo_ssh_command', {}).get('toggle', False) and ip_providers:
                machine_ex_ip_prov = random.choice(ip_providers)
                cosmetic_login_cmd = f"{cosmetic_login_cmd}" \
                                     f"The external IP detected is: " \
                                     f"$( a=$( curl -s --connect-timeout 2 {machine_ex_ip_prov} )" \
                                     f";if [[ $? == 0 ]];then echo \"$a\";" \
                                     f"else echo \"Sorry, failed to resolve the external ip address " \
                                     f"via \'{machine_ex_ip_prov}\'.\" ; fi )"
            cosmetic_login_cmd = f"{cosmetic_login_cmd}\\n\\nCloud-profiler - The equivalent ssh command is:" \
                                 f"\\nssh {ip_for_connection} {script_config['Local']['SSH_base_string']}"
            if shard_key_path:
                cosmetic_login_cmd = f"{cosmetic_login_cmd} -i {shard_key_path}"
            if con_username and not con_username == "<default>":
                cosmetic_login_cmd = f"{cosmetic_login_cmd} -l {con_username.replace('<', '').replace('>', '')}"
            if machine.con_port:
                cosmetic_login_cmd = f"{cosmetic_login_cmd} -p {machine.con_port}"
            if bastion_for_profile:
                if bastion_user:
                    cosmetic_login_cmd = f"{cosmetic_login_cmd} -J " \
                                         f"{bastion_user}@{bastion_for_profile}:{machine.bastion_con_port}"
                else:
                    cosmetic_login_cmd = f"{cosmetic_login_cmd} -J {bastion_for_profile}:{machine.bastion_con_port}"
            cosmetic_login_cmd = f"echo -e \"{cosmetic_login_cmd}\\n\""
            if login_command:
                login_command_fin = f"{cosmetic_login_cmd}; {login_command}"
            else:
                login_command_fin = f"{cosmetic_login_cmd}; " \
                                    f"{script_config['Local']['Moba']['echo_ssh_command']['assumed_shell']}"
        else:
            login_command_fin = login_command
        if connection_type == "#91#4%":
            profile = (
                f"\n{short_name} = {connection_type}{ip_for_connection}%{machine.con_port}%"
                f"{con_username}%0%-1%-1%{login_command_fin}{bastion_for_profile}%{machine.bastion_con_port}"
                f"%{bastion_user}%"
                f"%{shard_key_path}"
                f"1%0%%-1%%-1%0%0%-1%0%-1"
                f"{pcolors}"
                f"%80%24%0%1%-1%"
                f"<none>%%0%1%-1#0#"
                f" {tags} #-1\n"
            )
        else:
            profile = (
                f"\n{short_name} [{machine.id}] = {connection_type}{ip_for_connection}%{machine.con_port}%"
                f"{con_username}%%0%-1%{login_command_fin}%{bastion_for_profile}%{machine.bastion_con_port}"
                f"%{bastion_user}%0%"
                f"0%0%{shard_key_path}%%"
                f"-1%0%0%0%0%1%1080%0%0%1"
                f"{pcolors}"
                f"%80%24%0%1%-1%"
                f"<none>%%0%1%-1#0# {tags}      #-1\n"
            )
        profiles += profile
        bookmark_counter += 1
    with open(
            os.path.expanduser(
                os.path.join(
                    CP_OutputDir,
                    "CP-Moba.mxtsessions"
                )
            ),
            'wt'
    ) as handle:
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
            connection_command = f"{script_config['Local']['SSH_command']}"
            machine.tags = [f"Account: {machine.instance_source}, {machine.ip}"]
            for tag in machine.iterm_tags:
                machine.tags.append(tag)

            if machine.ip is None or "Sorry" in machine.ip:
                # If the IP is missing or unknown, do not connect
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
                    connection_command = f"function random_unused_port {{ local port=$( echo " \
                                         f"$((2000 + ${{RANDOM}} % 65000))); (echo " \
                                         f">/dev/tcp/127.0.0.1/$port) &> /dev/null ; if [[ $? != 0 ]] ; then export " \
                                         f"RANDOM_PORT=$port; else random_unused_port ;fi }}; " \
                                         f"if [[ -n ${{RANDOM_PORT+x}} && -n \"$( ps aux | grep \"ssh -f\" " \
                                         f"| grep -v grep | awk \'{{print $2}}\' )\" ]]; " \
                                         f" then kill -9 $( ps aux | grep \"ssh -f\" | grep -v grep " \
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
                connection_command = f"echo \"\\nThe Windows password on record is:\\n" \
                                     f"{machine.password[1].rstrip()}\\n\\n\" " \
                                     f"\n;echo -n '{machine.password[1].rstrip()}' " \
                                     f"|pbcopy; echo \"\\nIt has been sent to your clipboard for easy pasting\\n\\n\"" \
                                     f";{connection_command}"

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

                if machine.login_command and not machine.login_command == "null":
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
                print(f'Cloud-profiler - Working on static profile: {name}')
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
                    print('ERROR: There was a problem when updating the Docker context.\n', err)


def update_ssh_config(dict_list):
    ssh_conf_file = empty_ssh_config_file()
    for machine in dict_list:
        name = f"{machine.name}-{machine.ip}-{machine.id}"
        if machine.platform == 'windows':
            print(f"Cloud-profiler - SSH_Config_create - Skipping this {name}, as it is a Windows machine.")
            continue
        if (machine.instance_use_ip_public or not machine.bastion) and not machine.ip_public == '':
            ip_for_connection = machine.ip_public
        else:
            ip_for_connection = machine.ip
        ssh_conf_file.add(
            name,
            Hostname=ip_for_connection,
            Port=machine.con_port,
        )
        if machine.con_username:
            ssh_conf_file.set(name, User=machine.con_username)
        if (isinstance(machine.bastion, str) and not machine.instance_use_ip_public) \
                or machine.instance_use_bastion:
            ssh_conf_file.set(name, ProxyJump=machine.bastion)
        if machine.ssh_key and machine.use_shared_key:
            shard_key_path = os.path.join(
                os.path.expanduser(script_config["Local"].get('ssh_keys_path', '.')),
                machine.ssh_key
            )
            ssh_conf_file.set(name, IdentityFile=shard_key_path)
        print(f"Cloud-profiler - SSH_Config_create - Added {name} to SSH config list.")
    ssh_conf_file.write(CP_SSH_Config)


def aws_profiles_from_config_file(script_config_f, instance_counter_f, cloud_instances_obj_list_f):
    processes = []
    if not script_config_f['AWS'].get('profiles', None)[0] is None:
        for profile in script_config_f['AWS']['profiles']:
            print(f"Cloud-profiler - AWS: Working on {profile['name']}")
            if isinstance(profile.get("role_arns", False), dict):
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
            else:
                role_arn_s = False
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


def aws_profiles_from_awscli_config(aws_script_config):
    if os.path.exists(os.path.expanduser(aws_script_config['AWS']['aws_credentials_file'])):
        config.read(os.path.expanduser(aws_script_config['AWS']['aws_credentials_file']))
        for i in config.sections():
            if i not in aws_script_config['AWS']['exclude_accounts']:
                print(f'Cloud-profiler - Working on AWS profile from credentials file: {i}')
                get_ec2_instances(profile=i,
                                  ec2_instance_counter=instance_counter,
                                  ec2_script_config=aws_script_config
                                  )


def do_worker(do_script_config, do_instance_counter, do_cloud_instances_obj_list):
    for profile in do_script_config['DO']['profiles']:
        print(f"Cloud-profiler - DO: Working on {profile['name']}")
        get_do_instances(profile, do_instance_counter, do_script_config, do_cloud_instances_obj_list)


def linode_worker(linode_script_config, linode_instance_counter, linode_cloud_instances_obj_list):
    for profile in linode_script_config['Linode']['profiles']:
        print(f"Cloud-profiler - Linode: Working on {profile['name']}")
        get_linode_instances(
            profile,
            linode_instance_counter,
            linode_script_config,
            linode_cloud_instances_obj_list
        )


def esx_worker(esx_script_config, esx_instance_counter, esx_cloud_instances_obj_list):
    p_esx_list = []
    for profile in esx_script_config['ESX']['profiles']:
        print(f"Cloud-profiler - ESX: Working on \"{profile['name']}\"")
        if esx_script_config['ESX'].get('disable_ssl_cert_validation', True) or \
                profile.get('disable_ssl_cert_validation', True):
            disable_ssl_cert_validation = True
        else:
            disable_ssl_cert_validation = False
        profile_url = f"https://{profile['address']}:{profile.get('port', 443)}"
        if not checkinternetrequests(
                url=profile_url,
                verify=(not disable_ssl_cert_validation),
                vanity=f"ESX.{profile['name']}",
                terminate=True):
            return False
        esx_p = th.Process(
            target=get_esx_instances_list,
            args=(
                profile,
                esx_instance_counter,
                esx_script_config,
                esx_cloud_instances_obj_list,
                disable_ssl_cert_validation
            )
        )
        esx_p.start()
        p_esx_list.append(esx_p)

    for _ in p_esx_list:
        _.join()


def checkinternetrequests(url='http://www.google.com/', timeout=3, verify=False, vanity="internet", terminate=True):
    if url == 'http://www.google.com/':
        print(f"Cloud-profiler - Connectivity - Testing \"{vanity}\" connectivity (http://www.google.com/)")
    else:
        print(f"Cloud-profiler - Connectivity - Testing connectivity to \"{vanity}\" ({url})")
    try:
        if not verify:
            requests.packages.urllib3.disable_warnings(
                category=urllib3.exceptions.InsecureRequestWarning
            )
        requests.head(
            url,
            timeout=timeout,
            verify=verify
        )
        return True
    except socket.error as ex:
        print(f"Cloud-profiler - Connectivity - {ex}")
        print(
            f"Cloud-profiler - Connectivity - This means there was no connectivity to \"{vanity}\"...\n"
            f"Cloud-profiler - Connectivity - This thread has gone into haven ({vanity}).")
        if terminate:
            exit()
        else:
            return False


# MAIN
if __name__ == '__main__':
    VERSION = "v7.1.0_Alanis_Jagged"
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
            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0  # Get current, not default value

            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)

            CP_OutputDir = os.path.join(buf.value, "Cloud_Profiler")
        else:
            CP_OutputDir = "~/Library/Application Support/iTerm2/DynamicProfiles/"
        print(f"Cloud-profiler - CP_OutputDir to be used: {CP_OutputDir}")

        if not os.path.isdir(os.path.expanduser(CP_OutputDir)):
            os.makedirs(os.path.expanduser(CP_OutputDir))

        # From user home directory
        script_config = {}
        script_config_user = {}
        if not platform.system() == 'Windows' and not os.environ.get('CP_Windows', False):
            home_dir = "~/.iTerm-cloud-profile-generator/"
        else:
            home_dir = CP_OutputDir
        if os.path.isfile(os.path.expanduser((os.path.join(home_dir, "config.yaml")))):
            print("Cloud-profiler - Found conf file in place")
            with open(os.path.expanduser((os.path.join(home_dir, "config.yaml")))) as conf_file:
                script_config_user = yaml.full_load(conf_file)
        else:
            if not os.path.isdir(os.path.expanduser(home_dir)):
                os.makedirs(os.path.expanduser(home_dir))
            shutil.copy2(os.path.join(script_dir, 'config.yaml'),
                         os.path.expanduser(home_dir))
            print(f"Cloud-profiler - Copy default config to home dir {os.path.expanduser(home_dir)}")

        for key in script_config_repo:
            script_config[key] = {**script_config_repo.get(key, {}), **script_config_user.get(key, {})}

        InstanceProfile.script_config = script_config

        username = getpass.getuser()
        config = configparser.ConfigParser()

        # Clean legacy
        if script_config["Local"].get("CNC", True):
            for entry in os.scandir(os.path.expanduser(CP_OutputDir)):
                if not entry.is_dir(follow_symlinks=False):
                    if "config.yaml" not in entry.name:
                        if "CP" not in entry.name or \
                                (not platform.system() == 'Windows' and not os.environ.get('CP_Windows', False)
                                 and VERSION not in entry.name):
                            os.remove(entry.path)

        p_list = []
        # Static profiles iterator
        if not platform.system() == 'Windows' and not os.environ.get('CP_Windows', False):
            p = mp.Process(
                name="update_statics",
                target=update_statics,
                args=(CP_OutputDir, script_config, VERSION,)
            )
            p.start()
            p_list.append(p)

        # ESX profiles iterator
        if script_config['ESX'].get('profiles', False):
            p = mp.Process(target=esx_worker, args=(script_config, instance_counter, cloud_instances_obj_list))
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
            if not script_config["Local"].get("On_prem_only", False):
                checkinternetrequests(
                    url="https://api.digitalocean.com",
                    vanity="DO",
                    terminate=True
                )
            p = mp.Process(target=do_worker, args=(script_config, instance_counter, cloud_instances_obj_list))
            p.start()
            p_list.append(p)

        if script_config['Linode'].get('profiles', False):
            if not script_config["Local"].get("On_prem_only", False):
                checkinternetrequests(
                    url="https://api.linode.com",
                    vanity="Linode",
                    terminate=True
                )
            p = mp.Process(
                target=linode_worker,
                args=(
                    script_config,
                    instance_counter,
                    cloud_instances_obj_list
                )
            )
            p.start()
            p_list.append(p)

        """Wait for all processes (cloud providers) to finish before moving on"""
        for _ in p_list:
            _.join(script_config['Local'].get('Subs_timeout', 60))
        profiles_update_list = []
        if platform.system() == 'Windows' or os.environ.get('CP_Windows', False):
            profiles_update_p = th.Process(
                target=update_moba,
                args=(
                    cloud_instances_obj_list,
                )
            )
            profiles_update_p.start()
            profiles_update_list.append(profiles_update_p)
        else:
            profiles_update_p = th.Process(
                target=update_term,
                args=(
                    cloud_instances_obj_list,
                )
            )
            profiles_update_p.start()
            profiles_update_list.append(profiles_update_p)

            # ssh_config
            if script_config['Local'].get('Docker_contexts_create'):
                profiles_update_p = th.Process(
                    target=docker_contexts_creator,
                    args=(
                        list(
                            cloud_instances_obj_list,
                        )
                    )
                )
                profiles_update_p.start()
                profiles_update_list.append(profiles_update_p)

        if script_config['Local'].get('SSH_Config_create'):
            print("Cloud-profiler - SSH_Config_create is set, so will create config.")
            User_SSH_Config = os.path.join(os.path.join(os.path.expanduser("~"), ".ssh"), "config")
            CP_SSH_Config = os.path.join(os.path.join(os.path.expanduser("~"), ".ssh"), "cloud-profiler")
            if not platform.system() == 'Windows' and not os.path.exists(User_SSH_Config):
                with open(User_SSH_Config, "w") as file:
                    file.write("")
                with open(User_SSH_Config) as f:
                    if f"Include ~/.ssh/cloud-profiler" in f.read():
                        print(
                            "Cloud-profiler - Found ssh_config include directive for CP in user's ssh config file, "
                            "so leaving it as is.")
                    else:
                        print("Cloud-profiler - Did not find include directive  for CP in user's ssh config file, "
                              "so adding it.")
                        line_prepender(User_SSH_Config, "Include ~/.ssh/cloud-profiler")
                profiles_update_p = th.Process(
                    target=update_ssh_config,
                    args=(
                        cloud_instances_obj_list,
                    )
                )
                profiles_update_p.start()
                profiles_update_list.append(profiles_update_p)
            else:
                print("Cloud-profiler - SSH_Config_create - This is a Windows native run, so skipping it.")
        else:
            print("Cloud-profiler - SSH_Config_create - \"SSH_Config_create\" is not set, so skipping it.")

        for _ in profiles_update_list:
            _.join()

        if os.path.exists('marker.tmp'):
            os.remove("marker.tmp")
        jcounter = json.dumps(instance_counter.copy(), sort_keys=True, indent=4, separators=(',', ': '))
        jcounter_tot = sum(instance_counter.values())
        print(
            f"\nCloud-profiler - Created profiles {jcounter}\nTotal: {jcounter_tot}"
        )
        print(f"\nWe wish you calm clouds and a serene path...\n")
