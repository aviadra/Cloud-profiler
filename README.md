# Cloud_Profiler

The purpose of this script is to connect to cloud providers and generate profiles for quick SSHing.
As of v1.3, both iTerm for MacOS and MobaXterm for Windows are supported
Currently the supported cloud providers, are AWS and Digital Ocean.
This project is a fork of [gmartinerro](https://gist.github.com/gmartinerro/40831c8874ebb32bc17711af95e1416b), which gave me a good starting point. With that said, this version doesn't change the hosts file, so that it can be run without sudo.

This project has some assumptions:
- The script runs on either MacOS (tested only on Catalina and Mojave) or Windows (tested on windows 10).
- You have [iTerm](https://iterm2.com/) installed when using a Mac.
- Your system has Docker, or python3 installed (if using the "system install" method).

# How to use

## Docker way (recommended)
As of v1.5, it is possible to run the script using a docker container. You can choose to build it yourself or pull from docker hub. The instructions will focus on the latter.

#### Run as a service
This is the recommended way of running the script. Running it with the below parameters will have docker ensure that it is always in the background (unless specifically stopped), and the default refresh rate is 5 minutes. The below also maps the configuration directory and iTerm profile directory into the container.

##### On MacOS

`docker run --init --restart=always -d -e CP_Service=True -v ~/Library/Application\ Support/iTerm2/DynamicProfiles/:/root/Library/Application\ Support/iTerm2/DynamicProfiles/ -v ~/.iTerm-cloud-profile-generator/config.yaml:/root/.iTerm-cloud-profile-generator/config.yaml aviadra/cp`

##### On Windoes

`docker run --init --restart=always -d -e CP_Windows=True -e CP_Service=True -v "%HOMEDRIVE%%HOMEPATH%"\Cloud_Profiler/:/root/Cloud_Profiler/ -v "%HOMEDRIVE%%HOMEPATH%"\.iTerm-cloud-profile-generator/config.yaml:/root/.iTerm-cloud-profile-generator/config.yaml aviadra/cp`


#### Run ad-hoc
It is absolutely possible to run the script on a per-needed bases (a.k.a. "ad-hoc"). To do so, simply issue the same command, only omitting the "-d", "-e CP_Service=True" and "--restart=always" parameters.

##### On MacOS

`docker run --init --rm -v ~/Library/Application\ Support/iTerm2/DynamicProfiles/:/root/Library/Application\ Support/iTerm2/DynamicProfiles/ -v ~/.iTerm-cloud-profile-generator/config.yaml:/root/.iTerm-cloud-profile-generator/config.yaml aviadra/cp`

##### On windoes

`docker run -it --init --rm -e CP_Windows=True -v "%HOMEDRIVE%%HOMEPATH%"\Cloud_Profiler/:/root/Cloud_Profiler/ -v "%HOMEDRIVE%%HOMEPATH%"\.iTerm-cloud-profile-generator\config.yaml:/root/.iTerm-cloud-profile-generator/config.yaml aviadra/cp`

Note: While not required, I've added to the above the "[--rm](https://docs.docker.com/engine/reference/run/#clean-up---rm)" option just for tightness.

You should be all set, just go to the Configuration section.

# Configuration files
There is a YAML configuration file within the repo that gives the default values for the script behavior.
On the first run of the script, a personal configuration file is created in `~/.iTerm-cloud-profile-generator/config.yaml`. So, you don't have to fork the repo in order to have your own settings. Settings in the personal file will take precedence over the default ones from the repo file.
Possible options within the configuration files are noted below.
Note: For convenience, the following values are accepted for "True": 'True', 'yes' and 'y', and for "False: 'False', 'no' and 'n'.

## Example configuration
While a valid sample configuration file is provided within the repo, the below configuration, is what I actually use as my daily driver (keys have been omitted).
```
Local:
  static_profiles: "./iTerm2-static-profiles"
  ssh_base_string: "-oStrictHostKeyChecking=no -oUpdateHostKeys=yes -oServerAliveInterval=30 -oAddKeysToAgent=no"
  con_username: ''
  bastion: ''
  ssh_keys_path: "~/.ssh"
  use_shared_key: False
  
AWS:
  exclude_regions: ["ap-southeast-1", "ap-southeast-2","sa-east-1","ap-northeast-1","ap-northeast-2","ap-south-1"]
  aws_credentials_file: "~/.aws/credentials"
  con_username: False
  bastion_con_port: 22
  use_ip_public: False
  skip_stopped: True
  exclude_accounts: []
  use_awscli_profiles: False
  update_hosts: False
  profiles:
    -
      name: "Company_TGT"
      aws_access_key_id: "AKIAW*********"
      aws_secret_access_key: "D5am******************"
      role_arns: {
        sts_oper: "arn:aws:iam::438**********:role/iTerm_RO_from_TGT",
        sts_devops: "arn:aws:iam::168**********:role/iTerm_RO_from_TGT",
        sts_haim: "arn:aws:iam::701**********:role/iTerm_RO_from_TGT",
      }

DO:
  profiles:
    -
      name: "The one"
      token: "secretspecialuniquesnowflake"
      use_ip_public: True
```

## Local options
These are settings that are local to your machine or you want to set globally for all clouds. You can set here most of the same directives as in the "tags" section, except the below ones (they don't make sense anywhere else):

`static_profiles` - Set the location of the "static profiles" on your computer. The default is to point to where the repo is.

`ssh_keys_path` - Set the location to get the "shared keys" from. The default is "~/.ssh"

## AWS options
These are settings for your AWS account/s. 

`use_awscli_profiles` - The script knows how to yank profiles from a standard awscli configuration. This directive toggles this behavior. The default behavior is to not use awscli profiles, with the value of "False".

`aws_credentials_file` - This directive sets the location of the "credentials" file, when using the awscli configurations. The "credentials" file is where the profile names and credentials are derived from for the connections. The default is "~/.aws/credentials"

`use_ip_public` - Toggles if the IPs for the connection should be the internal ones (with Bastion) or external ones. The default is to use internal ones with the value of "False".

`skip_stopped` - Toggles if profiles for stopped instances should be created. The default is to skip stopped instances with the value of "True".

`exclude_accounts` - This is a list of accounts that are in your awscli configuration but should be excluded from the lookup. The default is an empty array([]).

`exclude_regions` - This is a list of regions to be skipped from lookup. One might want to populate this list if there are regions that are not used regularly, as skipping them shortens the amount of time the script runs and reduces the amount of API calls to AWS.

### Profiles
`profiles` - This is an array of hashes that represents AWS profiles. The structure is: a hyphen to separate the hashes in the array. Each hash has the following keys: "name", "aws_access_key_id and "aws_secret_access_key". See the example in the "repo settings file". 
Note: The example is deliberately commented out, so that if you don't configure it the script will not encounter errors).

#### STS support
It is possible to define a profile that uses the [AWS Security Token Service(STS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html), to "login" to roles in other AWS accounts you have access to.
The way to define this, is to set the directive under the STS account profile. That is, you define a profile with secret and key, so the script can login to it normally, then the script will iterate over the "role_arns" array of hashes, to look for resources in other accounts.
See the example configuration in the repo configuration file.

`role_arns` - This is an array of hashes (key + value) of roles to assume in other accounts, to look for resources. The "key" of a hash will be used as part of the name of the "instance source" visible in the resulting profiles. The "value" of a hash is the ARN of the AWS role in another account that has access to resources.

`mfa_serial_number` - Identifies your hardware or virtual MFA device. This can be defined, if the role on the remote account requires MFA authentication. Note that this will prompt for each ARN in the "role_arns" array, as One Time Passwords(OTP) must be unique for every login ([citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)). See example configuration in repo configuration file.

## DO (Digital Ocean)
`profiles` - This is an array of hashes that represents DO profiles. The structure is: a hyphen to separate the hashes in the array. Each hash has the following keys: "name" and "token". See the example in the "repo settings file".
Note: The example is deliberately commented out, so that if you don't configure it the script will not encounter errors).

# Configuration directives from tags and/or configuration files
The script can change the end result of the connections/profiles it creates, due to tags discovered on the cloud or directives from the conf files.
These range from whether to use the public IP for the connection, to should a bastion be used or what the address of it should be.

## Precedence
The script tries to "resolve" the directives from several data sources. The further away from the instance the setting originates from, the less precedence it has.
With that said, the further away from the machine a setting is set, it’s scope will be more far reaching. For example, setting the "con_username" setting at the "Local" level in the configuration file, while it has the lowest precedence and will be overwritten by any other config level or tag, it will essentially be set for all machines for all providers, unless noted otherwise at a higher precedence level.

The precedence of directives, is:
1. On the instance itself as Tags.
2. On the instance's VPC as Tags.
3. At the "profile" level in config files.
4. At the Cloud provider level (e.g. AWS, DO), in the config files.
5. On the "Local" level in the configuration files.

### Tags
Directives can be set with tags on the instances. You can either use them as is, for example as they appear in the config files, or prefix them with either "Cloud_Profiler" or "iTerm_" (the latter is kept for compatibility and may be deprecated in a future release).
It is recommended to use the "Cloud_Profiler" prefix, as it just gives context to the person seeing the tags on the instance.
For example, `Cloud_Profiler_profile_parent_name` (the preferred method), `iTerm_profile_parent_name` (may be deprecated in a future release), and even just `profile_parent_name` are all acceptable forms of tagging.

Possible directives are:

`profile_parent_name` - Sets the profile to inherit colors and other settings from.

`bastion` - The address of the Bastion to be used to reach this VM. When setting the value of this setting to "no", the bastion will not be used.

`bastion_use` - When using "iTerm_ip_public", the bastion is not used. unless this tag is set with the value of "yes".

`use_ip_public` - Denote that this instance profile, should use the instance public IP for the connection. Setting this tag, also sets the profile to not use a bastion, unless the "iTerm_bastion_use" tag is set.

`con_username` - The username to add to the connection.

`con_port` - The port to add to the connection.

`use_shared_key` - Toggle the use of the shared key that was used to create the instance. While this is not recommended, this is where you usually start. The default is to not use the shared key with the value of "False".

`ssh_key` - The name of the key to use. If this is not defined, and the "use_shared_key" is set, the key name on the instance is used.

# Cloud side setup
In general, there really isn't anything you "need" to do on the clouds side. With that said, there are Things you can/should set on the cloud side to make the setup more specific.

## AWS setup
On AWS, the default configuration is to push you towards securing your connections and to use a [Bastion](https://docs.aws.amazon.com/quickstart/latest/linux-bastion/architecture.html#bastion-hosts) for everything. This can be changed in the configuration files or using TAGs that you can add to instances and/or VPCs. In general, it is recommended to "tattoo" the "iTerm_bastion" at the VPC level.
On AWS you set a tag by adding it to the desired resource, setting the "key" field to the name of the tag and in the "value" field the desired setting.
Note the credentials used for AWS, must have the following permissions: "ec2:DescribeVpcs", "ec2:GetPasswordData", "ec2:DescribeRegions" and "ec2:DescribeInstances".

## Digital Ocean
Digital Ocean's implementation of VPC is such that there isn't a way to set tags on it (that I have seen).
On DO, you set a tag by adding it to the instance. The format to be used is: "tag_name:value". Note that there are no spaces between the key and the value.
Also note, that underscores(_) in the value part of the tag are replaced with spaces, and dashes(-) are replaced with dots(.).
DO does has one special tag "iTerm_host_name", which changes the node's host name to the value in the tag.
Other than that, the tags are the same as for AWS.

For example:

`host_name:Incredible_name1`

`bastion_use:yes`

`bastion:1-1-1-1`

# MobaXterm setup
The way to get the profiles into Moba is not as automatic as it is for iTerm. With that said, the script will generate a "sessions" file, that you can import manually into Moba, or you can use the [shared sessions feature](https://mobaxterm.mobatek.net/documentation.html#3_1_6).
The default location of the generated configuration file is "~/Cloud_Profiler/Cloud-profiler-Moba.mxtsessions".

# iTerm setup
Again, in general you don't need to change anything in your iTerm configuration. With that said, it is recommended that you create in your iTerm, the profiles you're going to reference when using the "iTerm_dynamic_profile_parent_name" tag. if you don't, nothing major will happen, iTerm will simply use the default profile and throw some errors to the Mac's console log.

## RDP support for MacOS (optional)
The RDP support is based on your MAC's ability to open rdp URIs. That is iTerm will issue something like "open rdp://address-of-instance". Compatible programs are Microsoft Remote Desktop 8/10 available on the app store.


## Static profiles
The "Static profiles" feature of this script, allows you to centrally distribute profiles so that you can reference them with the "iTerm_dynamic_profile_parent_name" tag. For example, the two profiles in the repo, give the "Red Alert" and "Dracula" color schemas with my beloved keyboard shortcuts. They are installed for you in the dynamic profiles automatically, which makes it possible to reference them with the tag and get a clear distinction when you're on prod vs normal servers.
The static profiles can also be used as a shim for the cases where you want to distribute profiles that don't come from AWS. For example, you have some VMs on a local ESX. You can create their profiles and save them in the "static" directory, and they will be distributed to the rest of the repo users

The way to add/remove profiles, is to do so in the "iTerm2-static-profiles" directory within the repo. You get the profiles, by creating them the regular iTerm way (as explained below) and then using the "export to json" options at the bottom of the "profiles" tab in preferences.
You can also set this location in the configuration files, if the path "from the repo" if you need to.

## Profile creation within iTerm
In order to ease the setup, I've set the https://github.com/mbadolato/iTerm2-Color-Schemes, as a submodule, so many color schemes are available "out of the box". 
The instructions below are the regular iTerm way of creating profiles.
For example, to create "DRACULA" profile:
- Create a new profile by clicking the plus (+) sign, in the profiles section of the "preferences".
- Give it the name "DRACULA".
- Go to the "Colors" tab and click "Color Presets" drop-down menu.
- Click on "Import". It will open up a finder window. Go into the "schemes" folder within the sub-module folder.
- Choose "Dracula.itermcolors".
- Now the "DRACULA" schema is select-able in the dropdown list.
Note: The "Red Alert" profile, which I recommend for production servers is part of the "Static profiles", so you can just use it by making it the value of the "iTerm_dynamic_profile_parent_name" tag.

We wish you calm clouds and a serene path...


# Appendix
These are things that have been written, but do not belong in the spotlight.

# Environment variables
It is possible to change the default behavior of the scripts (service and updater) with environment variables. These can be set on the shell before running the script. When using docker, these can be passed to the container, using the -e parameter (it can be specified multiple times if needed). Possible variables are:

- CP_LoopInterval - This changes the amount of time the script waits between refreshes. The default is 300 (5 minutes).

- CP_Service - Toggles “service” behavior (infinite loop), so one can choose to run the script in “ad-hoc” or as a service (as shown in the above instructions.

- OutputDir - This changes the location, where the resulting profile files are created.

## System install (less recommended)
- Install requirements using pip

`pip3 install requirements.txt --user`

- Clone the repo

`git clone https://github.com/aviadra/iTerm-cloud-profile-generator`
- Using python3 run the script

`python3 ./iTerm-cloud-profile-generator/update-cloud-hosts.py`
- You need to setup your access keys per the instructions below and then run again. Once that's done, you should see the dynamic profiles populated in iTerm (cmd + O). Windows users, see instructions below.