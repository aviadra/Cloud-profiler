# iTerm-cloud-profile-generator

The purpose of this script, is to connect to cloud providers and generate iTerm profiles for quick SSHing.
Currently, AWS and Digital Ocean are supported.
This project, is a fork of [gmartinerro](https://gist.github.com/gmartinerro/40831c8874ebb32bc17711af95e1416b), which gave me a good starting point. With that said, this version doesn't change the hosts file, so that it can be run without sudo.

This project has some assumptions:
- The script runs on MacOS (tested only on Catalina and Mojave).
- You have [iTerm](https://iterm2.com/) installed.
- Your system has python3 installed.

# How to use
- Install requirements using pip

`pip3 install requirements.txt --user`

- Clone the repo

`git clone https://github.com/aviadra/iTerm-cloud-profile-generator`
- Using python3 run the script

`python3 ./iTerm-cloud-profile-generator/update-cloud-hosts.py`
- You should see the dynamic profiles populated in iTerm (cmd + O)

# RDP support (optional)
The RDP support is based on your MAC's ability to open rdp URIs. That is iTerm will issue something like "open rdp://address-of-instance". Compatible programs are Microsoft Remote Desktop 8/10 available on the app store.

# Configuration files (Optional)
There is a YAML configuration file within the repo that gives the default values for the script behavior.
On the first run of the script, a personal configuration file is create in `~/.iTerm-cloud-profile-generator/config.yaml`. So you don't have to fork the repo in order to have your own settings. Settings in the personal file will take precedence over the default ones from the repo file.
Possible options within the configuration files are noted below.
Note: For convenience, the following values are accepted for "True": 'True' and 'yes', and for "False: 'False' and 'no'.

## Local options
These are settings that are local to your Mac or you want to set globally for all clouds. You can set here most of the same directives as in the "tags" section, except the below ones (they don't make sense anywhere else):

`static_profiles` - Set the location of the "static profiles" on your computer. The default, is to point to where the repo is.

`ssh_keys_path` - Set the location to get the "shared keys" from. The default is "~/.ssh"

## AWS options
These are settings for your AWS account/s. 

`use_awscli_profiles` - The script knows how to yank profiles from a standard awscli configuration. This directive toggeles this behavior. The default behavior is to not use awscli profiles, with the value of "False".

`aws_credentials_file` - This directive sets the location of the "credentials" file, when using the awscli configurations. The "credentials" file is where the profile names and credentials are derived from for the connections. The default is "~/.aws/credentials"

`use_ip_public` - Toggles if the IPs for the connection should be the internal ones (with Bastion) or external ones. The default is to use internal ones with the value of "False".

`skip_stopped` - Toggles if profiles for stopped instances should be created. The default is to skip stopped instances with the value of "True".

`exclude_accounts` - This is a list of accounts that are in your awscli configuration, but should be be excluded from the lookup. The default is an empty array([]).

`exclude_regions` - This is a list of regions to be skipped from lookup. One might want to populate this list if there are regions that are not used regularly, as skipping them shortens the amount of time the script runs.

### Profiles
`profiles` - This is an array of hashes that represents AWS profiles. The structure is: a hyphen to separate the hashes in the array. Each hash has the following keys: "name", "aws_access_key_id and "aws_secret_access_key". See the example in the "repo settings file". 
Note: The example is deliberately commented out, so that if you don't configure it the script will not encounter errors).

#### STS support
It is possible to define a profile that uses the [AWS Security Token Service(STS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html), to "login" to roles in other AWS accounts you have access to.
The way to define this, is to set the directive under the STS account profile. That is, you define a profile with secret and key, so the script can login to it normally, then the script will iterate over the "role_arns" array of hashes, to look for resources in other accounts.
See the example configuration in the repo configuration file

`role_arns` - This is an array of hashes (key + value) of roles to assume in other accounts, to look for resources. The "key" of a hash will be used as part of the name of the "instance source" visible in the resulting profiles. The "value" of a hash is the ARN of the AWS role in another account that has access to resources.

`mfa_serial_number` - Identifies your hardware or virtual MFA device. This can be defined, if the role on the remote account requires MFA authentication. Note that this will prompt for each ARN in the "role_arns" array, as One Time Passwords(OTP) must be uniq for every login ([citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)). See example configuration in repo configuration file.

## DO (Digital Ocean)
`profiles` - This is an array of hashes that represents DO profiles. The structure is: a hyphen to separate the hashes in the array. Each hash has the following keys: "name" and "token". See the example in the "repo settings file".
Note: The example is deliberately commented out, so that if you don't configure it the script will not encounter errors).

# Configuration directives from tags and/or configuration files
The script can change the end result of the connections/profiles it creates, due to tags discovered on the cloud or directives from the conf files.
These range from wether to use the public IP for the connection, to should a bastion be used or what the address of it should be.

## Precedence
The script tries to "resolve" the directives from several data sources. The further away from the instance the setting originates from, the less precedence it has.
With that said, the further away from the machine a setting is set, it’s scope will be more far reaching. For example, setting the "con_username" setting at the "Local" level in the configuration file, while it has the lowest precedence and will be overwritten by any other config level or tag, it will essentially be set for all machines for all providers, unless noted otherwise at a higher precedence level.

The precedence of directives, is:
1. On the instance itself as Tags.
2. On the instance's VPC as Tags.
3. At the "profile" level in config files.
4. At the Cloud provider level (e.g AWS, DO), in the config files.
5. On the "Local" level in the configuration files.

### Tags
When setting the directives with tags, they have to be prefixed with "iTerm_".

Possible directives are:

`iTerm_dynamic_profile_parent_name` - Sets the profile to inherit colors and other settings from.

`iTerm_bastion` - The address of the Bastion to be used to reach this VM. When setting the value of this setting to "no", the bastion will not be used.

`iTerm_bastion_use` - When using "iTerm_ip_public", the bastion is not used. unless this tag is set with the value of "yes".

`iTerm_use_ip_public` - Denote that this instance profile, should use the instance public IP for the connection. Setting this tag, also sets the profile to not use a bastion, unless the "iTerm_bastion_use" tag is set.

`iTerm_con_username` - The username to add to the connection.

`iTerm_con_port` - The port to add to the connection.

`iTerm_use_shared_key` - Toggle the use of the shared key that was used to create the instance. While this is not recommended, this is where you usually start. The default is to not use the shared key with the value of "False".

`iTerm_ssh_key` - The name of the key to use. If this is not defined, and the "use_shared_key" is set, the key name on the instance is used.

# Cloud side setup
In general there really isn't anything you "need" to do on the clouds side. With that said, there are Things you can/should set on the cloud side to make the setup more specific.

## AWS setup
On AWS, the default configuration is to push you towards securing your connections and to use a [Bastion](https://docs.aws.amazon.com/quickstart/latest/linux-bastion/architecture.html#bastion-hosts) for everything. This can be changed in the configuration files or using TAGs that you can add to instances and/or VPCs. In general it is recommended to "tattoo" the "iTerm_bastion" at the VPC level.
On AWS you set a tag by adding it to the desired resource, setting the "key" field to the name of the tag and in the "value" field the desired setting.
Note the credentials used for AWS, must have the following permissions: "ec2:DescribeVpcs", "ec2:GetPasswordData", "ec2:DescribeRegions" and "ec2:DescribeInstances".

## Digital Ocean
Digital Ocean's implementation of VPC is such that there isn't a way to set tags on it (that I have seen).
On DO, you set a tag by adding it to the instance. The format to be used is: "tag_name:value". Note that there are no spaces between the key and the value.
Also note, that underscores(_) in the value part of the tag are replaced with spaces, and dashes(-) are replaced with dots(.).
DO does has one spacial tag "iTerm_host_name", which changes the node's host name to the value in the tag.
Other then that the tags are the same as for AWS.

For example:

`iTerm_host_name:Incredible_name1`
`iTerm_bastion_use:yes`
`iTerm_bastion:1-1-1-1`


# iTerm setup
Again, in general you don't need to change anything in your iTerm configuration. With that said, it is recommended that you create in your iTerm, the profiles you're going to reference when using the "iTerm_dynamic_profile_parent_name" tag. if you don't, nothing major will happen, iTerm will simply use the default profile and throw some errors to the Mac's console log.

## Static profiles
The "Static profiles" feature of this script, allows you to centrally distribute profiles so that you can reference them with the "iTerm_dynamic_profile_parent_name" tag. For example, the two profiles in the repo, give the "Red Alert" and Dracula color schemas with my beloved keyboard shortcuts. They are installed for you in the dynamic profiles automatically, which makes it possible to reference them with the tag, and get a clear distinction when you're on prod vs normal servers.
The static profiles can also be used as a shim for the cases where you want to distribute profiles that don't come from AWS. For example you have some VMs on a local ESX. You can create their profiles and save them in the "static" directory and they will be distributed to the rest of the repo users

The way to add/remove profiles, is to do so in the "iTerm2-static-profiles" directory within the repo. You get the profiles, by creating them the regular iTerm way (as explained below) and then using the "export to json" options at the bottom of the "profiles" tab in preferences.
You can also set this location in the configuration files, if the path "from the repo" if you need to.

## Profile creation within iTerm
In order to ease the setup, I've set the https://github.com/mbadolato/iTerm2-Color-Schemes, as a submodule, so many color schemes are available "out of the box". 
The instructions below are the regular iTerm way of creating profiles.
For example to create "DRACULA" profile:
- Create a new profile by clicking the plus (+) sign, in the profiles section of the "preferences".
- Give it the name "DRACULA".
- Go to the "Colors" tab and click "Color Presets" drop-down menu.
- Click on "Import". It will open up a finder window. Go into the "schemes" folder within the sub-module folder.
- Choose "Dracula.itermcolors".
- Now the "DRACULA" schema is select-able in the dropdown list.
Note: The "Red Alert" profile, which i recommend for production servers is part of the "Static profiles", so you can just use it by making it the value of the "iTerm_dynamic_profile_parent_name" tag.

We wish you calm clouds and a serene path...
