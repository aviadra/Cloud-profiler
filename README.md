# Cloud_Profiler

# TL; DR
For most use cases, the installation is simply:

`bash <(curl -s https://raw.githubusercontent.com/aviadra/Cloud-profiler/main/startup.sh)`

# Intro
The purpose of this script is to connect to cloud providers and generate profiles for quick SSHing.

# Mini change-log
As of v1.3 ([Bankai](https://bleachfanfiction.fandom.com/wiki/Bankai)), both **iTerm** for MacOS and **MobaXterm** for Windows, are supported.
Currently, the supported cloud providers are AWS and Digital Ocean.

As of v2.0 ([Kaze no Kizu](https://inuyasha.fandom.com/wiki/Kaze_no_Kizu)) it can also create **SSH config file** entries
and **[Docker contexts](https://docs.docker.com/engine/context/working-with-contexts/)** that tunnel over SSH.

As of v3.0.2 ([How the mighty have fallen](https://en.wiktionary.org/wiki/how_the_mighty_have_fallen)),
  it is with a heavy heart, that I have switched from using VScode to using
[IDAE](https://www.jetbrains.com/?from=https://github.com/aviadra/Cloud-profiler).
After I asked, they have kindly provided me with a free "all pack" license,
  and I have found it to be a better tool for Python multiprocessor/multithreaded development.
  As well as very helpful with adhering to styling guides (like PEP8, but much more). 

As of v4.3.0 ([Tenteikūra](https://bleach.fandom.com/wiki/Tenteik%C5%ABra)),
  the docker installer supports all mainstream CPU architectures in addition to the regular x86/x64.
So it now works out of the box with "Apple M1" and other ARM based compute systems (like the raspberry pi),
  among other architectures.

As of v5.0 ([Hakuteiken](https://bleach.fandom.com/wiki/Sh%C5%ABkei:_Hakuteiken)), 
  Windows WSLv2 support introduced
  in order to make Windows more of a first class citizen then it was until now. 
This Hakuteiken [dove](https://en.wikipedia.org/wiki/Doves_as_symbols),
  is an [olive branch](https://en.wikipedia.org/wiki/Olive_branch) to all Windows users (myself mainly apparently... :)
WSL2 is also the recommended supported method of working with Windows, as it gets the most testing.
Note: Right now on Windows, the user uid for the container is always root, due to integration with the host issues.

As of v6.0 (Chasey Lain)[https://www.youtube.com/watch?v=If9fC9aJd-U] rudemnty ESXi support has been added.

## This project has some assumptions
- Your system has Docker, or python3 installed (if using the "system install" method).
- When using a Mac, You have [iTerm](https://iterm2.com/) installed.
- When using Windows, you have [MobaXterm](https://mobaxterm.mobatek.net/) installed.

## Getting started

### Docker way (recommended)
As of v1.5, it is possible and recommended, to run Cloud_profiler using a docker container.
You can choose to build it yourself or pull from docker hub. The instructions will focus on the latter.

Assuming you have Docker installed (on Windows preferably with [WSL2](https://docs.docker.com/docker-for-windows/wsl/)),
  issuing the below command will download the required container. 
It will also run Cloud_profiler as a service that refreshes the profiles every 5 minutes. 

If this is your very first run, the startup script will set you up with the basic static profiles, 
It will also copy the example configuration file to your home directory, 
  where you can edit it with your personal settings (like keys and features you'd like to toggle).
Simply run the below one liner and follow the on screen instructions:

`bash <(curl -s https://raw.githubusercontent.com/aviadra/Cloud-profiler/main/startup.sh)`

##### Trigger an update

If for what ever reason you don't want to wait the 5 minutes until the service updates the profiles,
  you can trigger it manually.
You can simply issue the "install command" from the TL;DR.

Or alternatively, you can use the "Update profile" that now exists for both iTerm and Mobaxterm.
You invoke this profile just like any other.

## Configuration files
There is a YAML configuration file within the repo that gives the default values for the script behavior.
On the first run of the script, if a personal configuration is missing,
it will be created in `~/.iTerm-cloud-profile-generator/config.yaml`.
As of v5.0 [Hakuteiken](https://bleach.fandom.com/wiki/Sh%C5%ABkei:_Hakuteiken), for Windows this will be Cloud_Profiler under the Documents foler of your user's home directory.
For example: C:\Users\aviad\Documents\Cloud_Profiler.
So, you don't have to fork the repo in order to have your own settings.
Settings in the personal file will take precedence over the default ones from the repo file.
See below for possible options of the configuration file.
Note: For convenience, the following values are accepted for "True":
'True', 'yes' and 'y', and for "False: 'False', 'no' and 'n'.

## Example configuration
While a valid sample configuration file is provided as a file within the repo,
the below configuration is what I actually use as my daily driver (keys have been omitted).
For some cases it is easier to copy from here, so here you go:
```YAML
Local:
  Static_profiles: "./iTerm2-static-profiles"
  SSH_base_string: "-oStrictHostKeyChecking=no -oUpdateHostKeys=yes -oServerAliveInterval=30 -oAddKeysToAgent=no"
  # Con_username: "ec2-user"
  # Bastion_Con_username: "aviadcye"
  Bastion: False
  SSH_keys_path: "~/Downloads"
  Use_shared_key: False
  Login_command: "sudo -i"
  Parallel_exec: True
  Skip_stopped: True
  Badge_info_to_display:
    Name: "Formatted"
    Instance_key: True
    InstanceType: True
    Bastion: False
    Bastion_Con_port: False
    Bastion_Con_username: False
    Con_port: False
    Con_username: False
    Dynamic_profile_parent: False
    Group: False
    Id: True
    Instance_use_Bastion: False
    Instance_use_ip_public: False
    Iterm_tags_prefixs: ["ENV"]
    # Iterm_tags_prefixs: []
    Password: False
    Platform: False
    Region: True
    SSH_key: False
    Use_shared_key: False
    VPC: False
    Ip_public: True
  Docker_contexts_create: False
  SSH_Config_create: True

AWS:
  exclude_regions: ["ap-southeast-1", "ap-southeast-2","sa-east-1","ap-northeast-2","ap-south-1"]
  aws_credentials_file: "~/.aws/credentials"
  Con_username: False
  Bastion_Con_port: 22
  instance_use_ip_public: False
  Skip_stopped: True
  exclude_accounts: []
  use_awscli_profiles: False
  update_hosts: False
  profiles:
    -
      name: "Work_account"
      aws_access_key_id: "EWRSGDY$#^FDERH"
      aws_secret_access_key: "#@$%@#GSRDFGBE%^$##%$DF"
      role_arns: {
        dev: "arn:aws:iam::946*********:role/iTerm_RO_from_TGT",
        oper: "arn:aws:iam::438*********:role/iTerm_RO_from_TGT",
        devops: "arn:aws:iam::168*********:role/iTerm_RO_from_TGT",
        haim: "arn:aws:iam::701*********:role/iTerm_RO_from_TGT",
      }
    -
      instance_use_ip_public: True
      name: "My_account"
      aws_access_key_id: "ASDAS%#@SDFGSDFDFSG"
      aws_secret_access_key: "FDGDFG#$%#SDFVSDGFSFDGW@#$%"

DO:
  instance_use_ip_public: True
  profiles:
    -
      name: "Work_account"
      token: "snow"
    -
      name: "My_account"
      token: "flake"
      Con_username: root
```

## Local options
These are settings that are local to your machine, or you want to set globally for all clouds.
You can set here most of the same directives as in the "tags" section,
except the below ones (they don't make sense anywhere else):

`CNC` - Added in version 4.0, and short for
[command and conquer](https://www.ea.com/games/command-and-conquer) (no affiliation),
Toggles the "dominate the dynamic profiles directory".
When this is turned on, files in the iTerm dynamic profiles directory that don't comply with CP's format are deleted.
The default behaviour is "on",
as I have yet to have met anyone who both uses my script and populates this directory with their own stuff.   

`SSH_command` - Introduced in version 4.1, this allows you to set the command to issue for SSHing. 
The default value is simply "ssh".

`SSH_Config_create` - Toggles the "create ssh config file" behavior. The default is false.

`Docker_contexts_create` - Toggles the "create Docker context" behavior - The default is false. 
Disclaimer: Turning this on will cause the container to be run with a root user internally and with a mount to the
local docker socket. This may have security implications, so turn this on at your own risk.

`Static_profiles` - Set the location of the "static profiles" on your computer.
The default is to point to where the repo is.
When running from a container, this is mapped to a directory on the host,
so if you change the location, you'll need to adjust your volume mounts 
(sorry, but I currently have no plan on helping with this).

`SSH_keys_path` - Set the location to get the "shared keys" from.
The default is "~/.ssh". Note that when running in a container.
Again, I recommend you use a personal key always for everything… This feature is here for “I have no choice” situations.

As of version 1.6.2, it is possible to set what information will be shown for an instance in the 
["badge"](https://www.iterm2.com/documentation-badges.html) area.
The repo configuration file comes with all possible values for the individual badges.
However, as not all values are available for every instance type from every provider,
only applicable values are shown even if they have been toggled.
In general, the toggle is simply “True” or “False”. See the list below for details.
Removing the toggle completely is the same as setting it to False.
It is possible to change the order of the items in the badge, by simply reordering them in the configuration file.

`Name` - Toggles showing the instance name. It is possible to set this to "Formatted",
in order to get a line braked list of the name information.

`Cloud_profiler_Instance_key` - The Main IP associated with the instance.

`InstanceType` - The type/size of the instance. For example, t3.nano.

`Bastion` - The associated Bastion for this instance.

`Bastion_Con_port` - The Bastion connection port.

`Bastion_Con_username` - The username used to connect to the Bastion.

`Con_port` - The port used to connect to the instance.

`Con_username` - The username used to connect to the instance.

`dynamic_profile_parent` - The name of the Dynamic profile parent name.

`Id` - The instance ID

`Instance_use_Bastion` - Is the flag of using the Bastion set?

`Instance_use_Ip_public` - Is the flag of using the public IP set?

`Iterm_tags_prefixs` - Iterm_tags, are what iTerm uses for indexing and show as information in the instance.
It is possible to set this toggle to false so not show them at all.
Setting this toggle to an empty array([]), will simply show all the iTerm tags given to the instance.
Given an array with values,
the shown values will be filtered to only show tags that start with the prefix of the strings in the array and
separated by a colon(:).
For example, for a tags “Id: id-123, ENV: prod, sg-groupname:sg-123123,
VPC: vpc-1231”, with the prefix filter of [“ENV”,”Id”], only “ENV: prod” and “Id: id-123” will be shown.

`Password` - If there is a password associated with the instance (windows) and decryption was possible,
show it in the badge.

`Platform` - Show the platform set for the instance (usually windows)

`Region` - Show the region of the instance.

`SSH_key` - Show the name of the SSH key associated with the instance at creation time.

`Use_shared_key` - Is the flag of using a shared key set?

`VPC` - The VPC id of the instance.

## AWS options
These are settings for your AWS account/s.

`use_awscli_profiles` - The script knows how to yank profiles from a standard awscli configuration.
This directive toggles this behavior. The default behavior is to not use awscli profiles, with the value of "False".

`aws_credentials_file` - This directive sets the location of the "credentials" file,
when using the awscli configurations. The "credentials" file is where the profile names and
credentials are derived from for the connections. The default is "~/.aws/credentials"

`use_Ip_public` - Toggles if the IPs for the connection should be the internal ones (with Bastion) or external ones.
The default is to use internal ones with the value of "False".

`Skip_stopped` - Toggles if profiles for stopped instances should be created.
The default is to skip stopped instances with the value of "True".

`exclude_accounts` - This is a list of accounts that are in your awscli configuration but should be excluded
from the lookup. The default is an empty array([]).

`exclude_regions` - This is a list of regions to be skipped from lookup.
One might want to populate this list if there are regions that are not used regularly,
as skipping them shortens the amount of time the script runs and reduces the amount of API calls to AWS.

### Profiles
`profiles` - This is an array of hashes that represents AWS profiles. The structure is:
a hyphen to separate the hashes in the array.
Each hash has the following keys: "name", "aws_access_key_id and "aws_secret_access_key".
See the example in the "repo settings file".

#### STS support
It is possible to define a profile that uses the
[AWS Security Token Service(STS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html),
to "login" to roles in other AWS accounts you have access to.
The way to define this, is to set the directive under the STS account profile.
That is, you define a profile with secret and key,
so the script can login to it normally,
then the script will iterate over the "role_arns" array of hashes, to look for resources in other accounts.
See the example configuration in the repo configuration file.

`role_arns` - This is an array of hashes (key + value) of roles to assume in other accounts, to look for resources.
The "key" of a hash will be used as part of the name of the "instance source" visible in the resulting profiles.
The "value" of a hash is the ARN of the AWS role in another account that has access to resources.

`mfa_serial_number` - Identifies your hardware or virtual MFA device.
This can be defined, if the role on the remote account requires MFA authentication.
Note that this will prompt for each ARN in the "role_arns" array, as One Time Passwords(OTP) must be unique for every
login ([citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)).
See example configuration in repo configuration file.

## DO (Digital Ocean)
`profiles` - This is an array of hashes that represents DO profiles.
The structure is: a hyphen to separate the hashes in the array.
Each hash has the following keys: "name" and "token". See the example in the "repo settings file".
Note: The example is deliberately commented out, so that if you don't configure it the script will not encounter errors).

## Configuration directives from tags and/or configuration files
The script can change the end result of the connections/profiles it creates,
  due to tags discovered on the cloud platform or directives from the conf files.
These range from whether to use the public IP for the connection,
  to should a Bastion be used or what the address of it should be.

## Precedence
The script tries to "resolve" the directives from several data sources.
The further away from the instance the setting originates from,
  the less precedence it has.
With that said, the further away from the machine a setting is set,
  it’s scope will be more far-reaching.
For example, setting the "Con_username" setting at the "Local" level in the configuration file,
  while it has the lowest precedence and will be overwritten by any other config level or tag,
  it will essentially be set for all machines for all providers, unless noted otherwise at a higher precedence level.

The precedence of directives, is:
1. On the instance itself as Tags.
2. On the instance's VPC as Tags.
3. At the "profile" level in config files.
4. At the Cloud provider level (e.g. AWS, DO), in the config files.
5. On the "Local" level in the configuration files.

## Cloud side setup
In general, there really isn't anything you "need" to do on the clouds side.
With that said, there are Things you can/should set on the cloud side to make the setup more specific.

### AWS setup
On AWS, the default configuration is to push you towards securing your connections and to use a 
[Bastion](https://docs.aws.amazon.com/quickstart/latest/linux-bastion/architecture.html#bastion-hosts) for everything.
This can be changed in the configuration files or using TAGs that you can add to instances and/or VPCs.
In general, it is recommended to "tattoo" the "Cloud_profiler_Bastion" at the VPC level.
On AWS, you set a tag by adding it to the desired resource, setting the "key" field to the name of the tag and in the
"value" field the desired setting.
Note the credentials used for AWS,
must have the following permissions: "ec2:DescribeVpcs", "ec2:GetPasswordData", "ec2:DescribeRegions"
and "ec2:DescribeInstances".

### Tags
Directives can be set with tags on the instances.
Note: As of v1.6.4, the capitalisation of the text in the tags after the prefix doesn't matter.

Possible directives are:

`Cloud_profiler_profile_parent_name` - Sets the profile to inherit colors and other settings from.
Note: If this profile doesn't exist locally, you will be getting nasty error messages from iTerm,
when iTerm tries to ingest the profile that points to it.

`Cloud_profiler_Bastion` - The address of the Bastion to be used to reach this VM.
When setting the value of this setting to "no", the Bastion will not be used.

`Cloud_profiler_Bastion_use` - When using "Cloud_profiler_Ip_public",
the Bastion is not used. unless this tag is set with the value of "yes".

`Cloud_profiler_instance_use_ip_public` - Denotes that this instance profile should use the instance public IP for the connection.
Setting this tag, also sets the profile to not use a Bastion, unless the "Cloud_profiler_Bastion_use" tag is set.

`Cloud_profiler_Con_username` - The username to add to the connection.

`Cloud_profiler_Con_port` - The port to add to the connection.

`Cloud_profiler_Use_shared_key` - Toggle the use of the shared key that was used to create the instance.
While this is not recommended, this is where you usually start.
The default is to not use the shared key with the value of "False".

`Cloud_profiler_SSH_key` - The name of the key to use. If this is not defined, and the "Use_shared_key" is set,
the key name on the instance is used.

### Digital Ocean
Digital Ocean's implementation of VPC is such that there isn't a way to set tags on it (that I have seen).
On DO, you set a tag by adding it to the instance. The format to be used is: "tag_name:value".
Note that there are no spaces between the key and the value.
Also note that the value part of the tag is processed with following rules:
1. Underscores(_) in the value part of the tag are replaced with spaces.
2. Dashes(-) are replaced with dots(.). This is done, 
     so you can write IPs within the tags despite the tag rules to not allow this.
   For example the IP of "1.1.1.1" would be represented as "1-1-1-1".
DO does have one special tag "iTerm_host_name", which changes the node's hostname to the value in the tag.
Other than that, the tags are the same as for AWS.

For example:

`host_name:Incredible_name1`

`Bastion_use:yes`

`Bastion:1-1-1-1`

## MobaXterm setup
You need to use the [shared sessions feature](https://mobaxterm.mobatek.net/documentation.html#3_1_6).
The default location of the generated configuration file is "%userprofile%\Documents\Cloud_Profiler\CP-Moba.mxtsessions".

## iTerm setup
Again, in general you don't need to change anything in your iTerm configuration.
With that said, it is recommended that you create in your iTerm,
the profiles you're going to reference when using the "iTerm_dynamic_profile_parent" tag.
If you don't, nothing major will happen.
However, as of v3.3.8 of iTerm, it will throw errors with popups.

### RDP support for MacOS (optional)
The RDP support is based on your MAC's ability to open rdp URIs. That is iTerm will issue something like
"open rdp://address-of-instance". Compatible programs are Microsoft Remote Desktop 8/10 available on the app store,
along others.
NOTE: Actually this stopped working (last tested on Big Sur).
I was going to fix it with a workaround of creating a file for the connection,
  and then having the RDP program open it, but then lost interest...

### Static profiles
The "Static profiles" feature of Cloud_profiler (currently only for MAC),
  allows you to centrally distribute profiles so that you can reference them with the "iTerm_dynamic_profile_parent"
tag. For example, the two profiles in the repo,
give the "Red Alert" and "Dracula" color schemes with my beloved keyboard shortcuts.
They are installed for you in the dynamic profiles automatically,
which makes it possible to reference them with the tag and get a clear distinction when you're on prod vs normal servers.
The static profiles can also be used as a shim for the cases where you want to distribute profiles that don't come from AWS.
For example, you have some VMs on a local ESX.
You can create their profiles and save them in the "static" directory,
and they will be distributed to the rest of the repo users

The way to add/remove profiles, is to do so in the "iTerm2-static-profiles" directory within the repo.
You get the profiles, by creating them the regular iTerm way (as explained below) and then using the "export to json"
options at the bottom of the "profiles" tab in preferences.
You can also set this location in the configuration files, in the path "from the repo" if you need to.

### Moba profile colors
As of v5.1.0, it is possible to set the color scheme the "static profiles" provide from the config files.
The "Red Alert" color palette is already set as an example in the repo's configuration file.
Use this example (noted below for convenience), as a reference when building a new one.
Unfortunately, there is no easy way to get the color values.
The way that I have found to get the values, is to create a profile with the desired settings,
  and reverse engineer it to extract the colors between "#MobaFont" and "%80%24%". 

### Profile creation within iTerm
As of v4.4.0, the inclusion of the [iTerm2-Color-Schemes repository](https://github.com/mbadolato/iTerm2-Color-Schemes),
has been removed. This both increased the container size, and was not convenient to use when tucked in the container.

The instructions below are the regular iTerm way of creating profiles.
For example, to create "DRACULA" profile:
- Create a new profile by clicking the plus (+) sign, in the profiles section of the "preferences".
- Give it the name "DRACULA".
- Go to the "Colors" tab and click "Color Presets" drop-down menu.
- Click on "Import". It will open up a finder window. Go into the "schemes" folder within the sub-module folder.
- Choose "Dracula.itermcolors".
- Now the "DRACULA" schema is select-able in the dropdown list.
Note: The "Red Alert" profile, which I recommend for production servers is part of the "Static profiles",
so you can just use it by making it the value of the "Cloud_profiler_dynamic_profile_parent" tag.

We wish you calm clouds and a serene path...

## Appendix
These are things that have been written, but do not belong in the spotlight.

## Environment variables
It is possible to change the default behavior of the scripts (service and updater) with environment variables.
These can be set on the shell before running the script. When using docker, these can be passed to the container,
using the -e parameter (it can be specified multiple times if needed). Possible variables are:

- CP_LoopInterval - This changes the amount of time the script waits between refreshes. The default is 300 (5 minutes).

- CP_Service - Toggles “service” behavior (infinite loop),
  so one can choose to run the script in “ad-hoc” or as a service (as shown in the above instructions.

- CP_OutputDir - This changes the location, where the resulting profile files are created.

## System install (less recommended)
- Clone the repo

`git clone https://github.com/aviadra/iTerm-cloud-profile-generator`
- Using python3 run the script

- Install requirements using pip

`pip3 install requirements.txt --user`

`python3 ./iTerm-cloud-profile-generator/update-cloud-hosts.py`
- You need to set up your access keys per the instructions below and then run again.
Once that's done, you should see the dynamic profiles populated in iTerm (cmd + O).
