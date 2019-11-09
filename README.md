# iTerm-cloud-profile-generator

The purpose of this script, is to connect to cloud providers and generate iTerm profiles for quick SSHing.
Currently, AWS and Digital Ocean are supported.
This project, is a fork of [gmartinerro](https://gist.github.com/gmartinerro/40831c8874ebb32bc17711af95e1416b), which gave me a good starting point. With that said, this version doesn't change the hosts file, so that it can be ran without sudo.

This project has some assumptions:
- The script runs on MacOS (tested only on Catalina and Mojave).
- You have [iTerm](https://iterm2.com/) installed.
- The awscli+ profiles and credentials are already setup on your system.
- You're SSHing to the machines with your own user + key.
- Your system has python3 installed.

# How to use
- Install requirements using pip

`pip3 install requirements.txt --user`

- Clone the repo

`git clone https://github.com/aviadra/iTerm-cloud-profile-generator`
- Using python3 run the script

`python3 ./iTerm-cloud-profile-generator/update-aws-hosts.py`
- You should see the dynamic profiles populated in iTerm (cmd + O)

# Configuration files (Optional)
There is a YAML configuration file within the repo that gives the default values for the script behaver.
On the first run of the script, a personal configuration file is create in `~/.iTerm-cloud-profile-generator/config.yaml`.  so you don't have to fork the repo in order to have your own settings. Settings in the personal file will take precedence over the default ones from the repo file.
Possible options within the configuration files are noted below.

## Local options
`static_profiles` - Set the location of the "static profiles" on your computer. The defualt, is to point to where the repo is.

## AWS options
`aws_credentials_file` - Sets the location to get the credentials files from which the profiles are deduced. The default is "~/.aws/credentials"

`use_ip_public` - Toggels if the IPs for the connection should be the internal whens (with Bastion) or external ones. the Defualt is to use internal ones with the value of "False".

`skip_stopped` - Toggels if profiles for stopped instaces should be vreated. The defualt is to skip stopped instances with the value of "True".

`exclude_accounts` - This is a list of accounts that are to be exluded from the lookup, even though you have a profiles for them. The default is an empty array([]).

`exclude_regions` - This is a list of regions to skipped from lookup. One might want to pupulate this list if there are regions that are not used regularly, as skipping them shortens the amount of time the script runs.

## DO
`token` - The token used to connect to DO's API. Default value is: "secretspecialuniquesnowflake"

# AWS setup
In general there really isn't anything you "need" to do on the AWS side. With that said, the default configuration is to push you towards securing your connections and to use a [Bastion](https://docs.aws.amazon.com/quickstart/latest/linux-bastion/architecture.html#bastion-hosts) for everything. This can be changed in the configuration files or using TAGs that you can add to instances and/or VPCs. In general it is recommended to "tattoo" the "iTerm_bastion" at the VPC level.
All the iTerm tags are prefixed with "iTerm". Some tags can be set on the VPC level noted in the description.
Possible tags for the script are:
`iTerm_dynamic_profile_parent_name` - Sets the profile to inherit colors and other settings from. [VPCable]

`iTerm_bastion` - Specifying this tag on an instance, overrides the VPC "default" one. [VPCable]

`iTerm_use_ip_public` - Denote that this instance profile, should use the public IP for the connection. Setting this tag, also sets the profile to not use a bastion, unless the "iTerm_bastion_use" tag is set.

`iTerm_bastion_use` - When using "iTerm_ip_public", the bastion is not used. unless this tag is set with the value of "yes".

# iTerm setup
Again, in general you don't need to change anything in your iTerm configuration. With that said, it is recommended that you create in your iTerm, the profiles you're going to reference when using the "iTerm_dynamic_profile_parent_name" tag. if you don't, nothing major will happen, iTerm will simply use the default profile and throw some errors to the Mac's console log.

## Static profiles
The "Static profiles" feature of this script, allows you to centrally distribute profiles so that you can reference them with the "iTerm_dynamic_profile_parent_name" tag. For example, the two profiles in the repo, give the "Red Alert" and Dracula color schemas with my beloved keyboard shortcuts. They are installed for you in the dynamic profiles automatically, which makes it possible to reference them with the tag, and get a clear distinction when you're on prod vs normal servers.
The static profiles can also be used as a shim for the cases where you want to distribute profiles that don't come from AWS. For example you have some VMs on a local ESX. You can create their profiles and save them in the "static" directory and they will be distributed to the rest of the repo users
TODO - Support other clouds

The way to add/remove profiles, is to do so in the "iTerm2-static-profiles" directory within the repo. You get the profiles, by creating them the regular iTerm way (as explained below) and then using the "export to json" options at the bottom of the "profiles" tab in preferences.
You can also set this location in the configuration files, if the path "from the repo" doesn't do what you need.

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
