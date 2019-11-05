# iTerm-cloud-profile-generator

The purpose of this script, is to connect to cloud providers (currently only AWS is supported) and generate iTerm profiles.
It is a fork of "https://gist.github.com/gmartinerro/40831c8874ebb32bc17711af95e1416b", which gave me a good starting point. With that said, currently this version of the script doesn't change the hosts file, so that it can be ran without sudo.

This project currently has some assumptions:
- When running "locally", the system is MacOS
- You have iTerm installed
- The awscli + profiles and credentials are already setup on your system and you're using the default locations for the configuration files.
- You have boto3 installed.
- Only running instances are used.
- You're connecting to the. machines connecting your own user + key.
- Your system has python3 installed.
- The default is to use internal IPs for instances (you can change this by adding the tag "ip_public") TODO.

# How to use (local)
- Install boto3 using pip

`pip3 install boto3 --user`

- Clone the repo

`git clone https://github.com/aviadra/iTerm-cloud-profile-generator`
- Using python3 run the script

`python3 update-aws-hosts.py`
- You should see the dynamic profiles populated in iTerm

# AWS setup
In general there really isn't anything you "need" to do on the AWS side. However seeing that by default only internal IPs are used, as they don't change and thus provide a fixed point (also original script behavior), you would have to be VPNed to the VPC in order to be able to connect to the instances. So there are TAGs you can add to instances and/or VPCs, to toggle script behavior. In general it is recommended to "tattoo" the "iTerm_bastion" at the VPC level.
All the iTerm tags are prefixed with "iTerm". Some tags can be set on the VPC level noted in the description.
Possible tags for the script are:
- iTerm_dynamic_profile_parent_name - Sets the profile to inherit colors and other settings from. Note that this script doesn't distribute/create the profiles, thats on you... [VPCable]
- iTerm_bastion - Specifying this tag on an instance, overrides the VPC "default" one. [VPCable]
- iTerm_use_ip_public - Denote that this instance profile, should use the public IP for the connection. Setting this tag, also sets the profile to not use a bastion, unless the "iTerm_bastion_use" tag is set.
- iTerm_bastion_use - When using "iTerm_ip_public", the bastion is not used. unless this tag is set with the value of "yes".

# iTerm setup
Again, in general you don't need to change anything in your iTerm configuration. With that said, it is recommended that you create the profiles you're going to reference when using the "iTerm_dynamic_profile_parent_name" tag. if you don't, nothing major will happen, iTerm will simply use the default profile and throw some errors to the logs.
In order to ease the setup, I've set the https://github.com/mbadolato/iTerm2-Color-Schemes, as a submodule. 
For example to create "DRACULA" profile:
- Create a new profile by clicking the plus (+) sign, in the profiles section of the "preferences".
- Give it the name "DRACULA".
- Go to the "Colors" tab and click "Color Presets" dropdown menu.
- Click on "Import". It will open up a finder window. Go into the "schemes" folder within the submodule folder.
- Choose "Dracula.itermcolors".
- Now the "DRACULA" schema is selectable in the dropdown list.
Note: The "Red Alert" profile, which i recommend for production servers is part of the "Static profiles", so you can just use it
