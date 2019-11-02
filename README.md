# iTerm-cloud-profile-generator

This project currently has some assumptions:
- When running "locally", the system is MacOS
- The awscli + profiles and credentials are already setup on your system and you're using the default locations for the configuration files.
- You're connecting to the machines connecting your own user + key.
- Your system has python3 installed
- The default is to use internal IPs for instances (you can change this by adding the tag "external_ip") TODO.

# How to use (local)
- Clone the repo

`git clone https://github.com/aviadra/iTerm-cloud-profile-generator`
- Change the permissions on the iTerm dynamic profiles directory, so that you can change it without invoking the script with sudo rights (TODO)

`chown $(whoami):staff /Application/iTerm/dynamic`
- Using python3 run the script

`python3 update-aws-hosts.py`
- You should see the dynamic profiles populated in iTerm

# AWS setup
In general there really isn't anything you "need" to do on the AWS side. With that said, there are TAGs you can add to instances and/or VPCs, to toggle script behavior.
- VPC tags
    - You can add the "bastion" tag to a VPC, and VMs within that VPC will automatically use it.
    - Default profile to inherit colors from TODO    
- Instance(VM) tags
  - You can specify the "bastion" tag. Doing so overrides the VPC "default" one.
  - You can use the "external_ip" tag to note that this instance profile, should use the public IP for the connection. TODO
    - When using "external_ip", the bastion is not used. unless you specify "bastion_use = yes".
