# Change Log

## v1.4.1
Changed bastion decision (again) so that it works as expected.
Removed unnecessary space after the ssh command 

## v1.4
Changed the names of tags one sets on instances to "Cloud_Provider".
PEP 498 the last of the "formats" have been removed.
Added setting Bastion username and port


## v1.3.1
Changed repo/project name from "iTerm-cloud-profile-generator" to "Cloud profiler"


## v1.3
Now supporting running on windows and creating "MobaXterm" profiles (test on v12.4)
Moved to use PEP 498 with f strings


## v1.2
Now supporting AWS STS configurations.
Changed session name to indicate that it was created by the script with which user and on what machine (for easy blaming via logs :)
Added the source of the instance to the Guid, to deliberately show duplicate configurations.
Removed "tagSplitter" for a better solution that doesn't cutoff tags.
Now handling SG tags for multiple network interfaces on instance.
Now giving a message when IP could not be found.


## v1.1.1
Fixed decryption key detection and added a more descriptive message on why the password could not be decrypted.
Added to Readme, the minimal set of permissions required for AWS.
Fixed "skip stopped" instances logic, and now supporting setting in config files as the "Local" level.


## v1.1
Moved DO section to be below generic functions.
Added function to decrypt password for a windows instance copied from [tinkerbotfoo](https://gist.github.com/tinkerbotfoo/337df5bd1faff777fb52).
Changed settingResolver to return True or False answers only, adjusted "generic tag extracting" funcs to match, and aligned all "if"s.
Added ability to set the skip stopped for AWS at the profile level.
Added instance counter.
Fixed Bastion decision (again).
Added PyCryptodome to requirements.


## v1.0.1
Added the ability to block the use of a bastion, by setting the tag iTerm_bastion to the value of "no".
Corrected DO bug not using Bastion.
Added self-healing for usage of random port by detecting an already established tunnel and killing it before trying to connect if the variable is already set.
Added ability to run without parallelization (mainly for debugging)