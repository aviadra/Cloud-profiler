import os
import random

def update_moba(
        obj_list,
        VERSION,
        instance_counter,
        script_config,
        CP_OutputDir
):
    profiles = "[Bookmarks]\nSubRep=\nImgNum=42"

    # update profile
    profiles += f"\n[Bookmarks_1]" \
                f"\nCP Update profiles {VERSION} =" \
                f";  logout#151#14%Default%%Interactive " \
                f"shell%__PTVIRG__[ -z ${{CP_Version+x}} ] " \
                f"&& CP_Version__EQUAL__'v6.1.1_Chasey_Pencive_Flitterby'__PTVIRG__[ -z ${{CP_Branch+x}} ] " \
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

        if "Sorry" in machine.ip:
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
        if script_config['Local'].get('Moba', {}).get('echo_ssh_command', {}).get('toggle', False) and \
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
                                 f"\\nssh {ip_for_connection}"
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