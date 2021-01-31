# Change Log
## v4.3.3 - Kōtotsu (Wresting-Surge)
Startup script cleanups to remove logic of not knowing the version and reduce restarts of conatiner

## v4.3.2 - Haien (Abolishing Flames)
Start of removing "master" branch. (It will be maintained for legacy compatabilety for now)

## v4.3.1 - Kakushitsuijaku (Footprint-Attentive Pursuing-Sparrows)
Seeing that the "Update profile" is the most likely path to become a beta tester,
I've removed the branch selection from the "TL;DR" installer.

## v4.3.0 - Tenteikūra (Heavenly Rickshaws in Silken Air)
Adding multi arch support!! (M1 mac users, you're welcome).
Moved to 3 digit versioning.
Changed the update profile file name to not contain the version for easier upgrades.

## v4.2 - Kurohitsugi (Black Coffin)
Moved to using Alpine as the base image to reduce CVEs.
Removing "sh" from the final form of the container required weaning off GNU usage.
Fixed docker contex creation to actually work.

## v4.1.3 - Nega Scott
SSH config - Bastions where not used when they should have been,

## v4.1.2 - Akuma
SSH config - bastions were self looping.

## v4.1.1 - Cero (Hollow Flash)
Fixed Docker context and SSH config creations (they were still using pre v4.0 methods to access data).

## v4.1 - Hōrin (Disintegrating Circle)
Added ability to set the ssh command to use from the config file.
Dockerfile: Added OS upgrade to lower CVEs.
Moved where we copy the requirements, 
so it doesn't invalidate the cache too soon and its visually closer to where it is used.
BUG: Corrected the name of the attribute we're looking for in the "script_config".
Added deleting the container if the version has changed (as indicated by the file name).
Reduced linting issues from "startup" script.
Updated README to include instructions about the new "SSH_command" directive, and for better readability.

## v4.0.1 - Tsuriboshi (Suspending Star)
Changed it so the value of the tag we're looking for, can be anywhere in the tag value we get from AWS.
The tag "dynamic_profile_parent_name" was changed to "dynamic_profile_parent", in order to not collide with the "Name"
tag.

## v4.0 - Daiyōkai (in a "class" of my own :)
Moved to using a "class" for the machines profiles instead of a nested dict ＼(｀0´)／.

Added "legacy cleaner"/"dynamic profile file versioner", to remove all files that don't match the current version. 

Many linting fixes with the help of [IDEA](https://www.jetbrains.com/?from=https://github.com/aviadra/Cloud-profiler).

Removed the "update_hosts" and "groups" features, that were imported from the original
[gist by gmartinerro](https://gist.github.com/gmartinerro/40831c8874ebb32bc17711af95e1416b). 

## v3.0.3
Traces of the old version leaked in and cause ppl to get the double guid error.

This version is mainly to force the deletion of all update profiles with the issue.

Also, removed the guid from the update profile all together, so this will not happen again.

## v3.0.2 - How the mighty have fallen (leaving VScode)
Now actually using threads within the subprocesses and Parallel_exec is no longer used (not even for debugging...
thank you Intellij)

Adjusted changelog to look more like it should (now that I have a builtin preview with intellij) 

## v3.0.1
Parallel_exec bug - This was set to False when I developed and skewed my results :\\

Changed the way we handle the creation of ssh config.

## v3.0 - Bakusaiga
Started using intellij Pycharm and IDEA.
Switched to using multiprocessing (instead of threads), dramatically improving the execution time,
as processes don't share the boto client connection state.

Fixed all pycharm suggestions for cleaner code.

## v2.0.2
Fixed SSH config directory error for new users that don't have any configuration yet.

## v2.0.1
Fixed windows detection typo

## v2.0 - Kaze no Kizu
Added creating docker contexts.

Added preliminary support for creating SSH configs.

Updated superlinter version used.

## v1.8.4
Added the tags "PrivateDnsName" and "ImageId" for AWS instances to be part of the information gathered.

Internal, Added repo linting as github action.

## v1.8.3
Update profiles now simply resets the "rest counter" instead of causing an out of turn execution.

## v1.8.2a
Cosmetic

## v1.8.2
Added limits on the size of the log file.

## v1.8.1
Changed it so on ad-hoc run, the service is only restarted when a container changes.

## v1.8
Meany changes to Startup script: moved to use zsh, heavily using functions and better error handing.

## v1.7.3
Update profile is now maintained by the startup script.

## v1.7.2
Update profile name changed, and the way it works synced with startup script. Also, startup script slight change.

## v1.7.1
Changed Startup script to be a bash file in the repo that is DLed using curl.

## v1.7
Added Startup/setup script.

Updated DockerFile and dockerignore to use best practices suggested by VScode (no root for example)

Updated "update" static profile, so it uses the new "appuser" paths.

Updated configuration file.

Updated documentation.


## v1.6.5
Added CP_Version variable, which if set (in your zshrc file for example) will be used to determine which version to pull

## v1.6.4 - Bankotsu
You get capitalisation, and you get capitalisation... everybody gets CAPITALISATION!!! ＼(｀0´)／

Added Login_command to be executed right after a login to the remote system. (Useful for automatically "sudo -i")

## v1.6.3
Added the "Update" profile to the "static" profiles in the repository.

## v1.6.2
Added Badge customization ^_^

## v1.6.1
Bumped python base version to latest

Removed install of time update as it seems to not work in a container

Some README updates due to improved docker usage.

## v1.6 - Sōryūha
Docker for windows support is now a first class citizen.

Moved to use multi-stage builds.

Fixed STS issue when system user has spaces.

STS assume role exception now gives the actual exception message from boto.

Now syncing container time with NTP before running, due to Windows finicky behavior.

## v1.5.1
Changed Docker base to use "python:slim-buster". This reduced the image size from 1.13G to 392M. \m/ (>_<) \m/

## v1.5 - Tokijin
Docker support :)

Changed placement of the profiles to be atomic due to change in iTerm 3.8.8
[#8679](https://gitlab.com/gnachman/iterm2/issues/8679).

Windows bug "missing setting of d, before use" fix.


## v1.4.1
Changed Bastion decision (again) so that it works as expected.

Removed unnecessary space after the ssh command

## v1.4
Changed the names of tags one sets on instances to "Cloud_Provider".

PEP 498 the last of the "formats" have been removed.

Added setting Bastion username and port


## v1.3.1
Changed repo/project name from "iTerm-cloud-profile-generator" to "Cloud_Profiler"


## v1.3 - Bankai
Now supporting running on windows and creating "MobaXterm" profiles (test on v12.4)

Moved to use PEP 498 with f strings


## v1.2
Now supporting AWS STS configurations.

Changed session name to indicate that it was created by the script with which user and on what machine
(for easy blaming via logs :)

Added the source of the instance to the Guid, to deliberately show duplicate configurations.

Removed "tagSplitter" for a better solution that doesn't cutoff tags.

Now handling SG tags for multiple network interfaces on an instance.

Now giving a message when IP could not be found.


## v1.1.1
Fixed decryption key detection and added a more descriptive message on why the password could not be decrypted.

Added to Readme, the minimal set of permissions required for AWS.

Fixed "skip stopped" instances logic, and now supporting setting in config files as the "Local" level.


## v1.1
Moved DO section to be below generic functions.

Added function to decrypt the password for Windows instance copied from
[tinkerbotfoo](https://gist.github.com/tinkerbotfoo/337df5bd1faff777fb52).

Changed settingResolver to return True or False answers only, adjusted "generic tag extracting" funcs to match,
and aligned all "if"s.

Added ability to set the skip stopped for AWS at the profile level.

Added instance counter.

Fixed Bastion decision (again).

Added PyCryptodome to requirements.


## v1.0.1 - Shikay
Added the ability to block the use of a Bastion, by setting the tag iTerm_bastion to the value of "no".

Corrected DO bug not using Bastion.

Added self-healing for usage of random port by detecting an already established tunnel and killing it before trying to
connect if the variable is already set.

Added ability to run without parallelization (mainly for debugging)