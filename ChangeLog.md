# Change Log
## v6.1.2 - [Chasey Pencive Gil](https://wiki.python.org/moin/GlobalInterpreterLock)
Version name thoughts: It seems the move to python 3.10.0, didn't bring the improvement I was after, 
and Cloud profiler's container was still
getting hung on random. the only thing I found so far that consistently helps,
is switching the threads in the main section to be process instead. 
I can only guess that not all threads are born equal in the eyes of the 
[Gil](https://wiki.python.org/moin/GlobalInterpreterLock)?

Also Pencive is still to young to go.


## v6.1.1 - [Chasey Pencive Flitterby](https://harrypotter.fandom.com/wiki/Flitterby)
Version name thoughts: Right after release, Shira has brought to my attention that I have introduced a bug, and [Pencive](https://harrypotterwizardsunite.fandom.com/wiki/Pensieve)
is such a good name it's a shame to let it go so soon, so I didn't.

I was trying to make it so the 
SSH config file will be created for the user automatically. 
However, I forgot to add the "only if it doesn't exist" part...

Even the wings of a tiny Flitterby can change the world with one innocent flap.



CP in Moba mode, is now able to ask a provided list of external ip providers for the "real" external IP of the machine.

## v6.1.0 - [Chasey Pencive](https://harrypotterwizardsunite.fandom.com/wiki/Pensieve)
Version name thoughts: Girls give me a name for something that shows you information you already know -> 
[Pencive](https://harrypotterwizardsunite.fandom.com/wiki/Pensieve).

Note: "Asking the girls" be like asking [teletraan1](https://youtu.be/MiFxHUHY83Q?t=954).

Pencive: Windows users now get vanity information (if toggled in settings) for easier access to the information gathered 
by CP.

Added better resolve of where the "documents" folder is for windows (onedrive support).

Improved the native Windows run.

Moved to Python 3.10.0 as the alpha version had issues with threads.

Added protections for AWS stuff not being present 
(Who are you, that uses CP only for DO... but if you're not me, let me know...).

Another contribution by Eyal to make "sorry" more durable (committed on his behalf).

Config file now gives the correct default directive for "instance use public ip".

Removed Python packages version pinning. I'm distributing a finished and working container...
I want my stuff to always be on the latest greatest and as few CVEs as possible. 
if anyone wants to "build" it from scratch and this causes issues, 
they should "deal with it" and return the results to us per GPL.

## v6.0.9 - [Chasey Butō](https://bleach.fandom.com/wiki/But%C5%8D)
Version name thoughts: Null -> null step (Butō) -> TTS Butō (sounds like butt) -> Chasey butt?? how can I resist?

Added the ability to put the value of the "Login_command" tag to "null", as a way to disable it.
This was needed, because when tagging on DO, it was not possible to use the regular empty string 
(as I have been doing on AWS), as DO simply doesn't allow it.

## v6.0.4-8 - [Chasey Bit](https://freqtrade.io/)
Version name thoughts: This past couple of months I've been chasing the Bitcoin with a trading bot so havn't invested in Cloud-profiler...
Also, this is only a little "bit" of change :)

Updated the python/alpine base (seems Github doesn't like all python images, and python doesn't support s390x anymore for some reason).

Snyk: updated jsonpickle

Restored "sh" on container (you already have python... who am I kidding?)

Connectivity checker to default to verifying SSL.

Improved the way tailing logs works


## v6.0.3 - [Chasey Amy](https://en.wikipedia.org/wiki/Chasing_Amy)
Version name thoughts: Chasey... -> Chasing.... -> Chasing Amy -> [Intergalactic civil war?](https://www.youtube.com/watch?v=v3XTHVC1Nf0)

There was a bug where only the first ESX entry would be processed.
All ESXs are now taken into account and are threaded.

Threading and processes have gotten a face lift to make the entire run even faster and take less resources.

Development abilities added to Windows version of the update profile.


## v6.0.2 - [Chasey Penny](https://en.wikipedia.org/wiki/Penny_(The_Big_Bang_Theory))
Version name thoughts: Chasey Lain... Lain... Penny Lain... jcpenney -> google -> Window & Home Decor... 
Yes that is what I've done in this version...

ESX: Added a better check for guest being "Windows".
Corrected, RDP profile building.

Corrected "pcolors" to not include "f" (ha?).

Dockerfile optimizations to make the build (especially from scratch) faster.

## v6.0.0/1 - [Chasey Lain](https://www.youtube.com/watch?v=If9fC9aJd-U)
Version name thoughts: Even though it's aging, ESX is still the best on-prem hypervisor... 
Just like "Chasey Lain" in her profession? ¯\_(ツ)_/¯.
No but seriously, 
  due to the line "This thread has gone into haven", 
  which was added in this version and come from ["Fire Water Burn"](https://www.youtube.com/watch?v=Adgx9wt63NY) 
  by the same band... So very close memory address that to me come in "chunks"... 
Seeing that I had to split the ESX VM retrieve into "chunks" (so it takes less time), it seemed only fitting...

Changes:

ESX_support init.

Now checking if the specific API provider is available before trying to use it

AWS regions section, now use threads for even more speed.

Added a default timeout.
This doesn't allow any cloud provider to take more than this time and lock the generation of the profiles for all the others.


## v5.3.1 - [Actual](https://en.battlestarwikiclone.org/wiki/Actual) [Adama](https://en.wikipedia.org/wiki/William_Adama)
Version name thoughts: A fresh installation brings you back to earth (adama means earth in hebrew).

Changes:

Seams we've created the directory separately from copying the static profiles... 
I don't know this work for ppl until now, 
  but I guess there simply wasn't a truly fresh installation until now...

## v5.3.0 - [Actual](https://en.battlestarwikiclone.org/wiki/Actual)
Version name thoughts: While I don't use the ssh config method as much as others, 
  it is the most basic method of connecting... So if you're one of the people who insist like
  [Adama](https://en.battlestarwikiclone.org/wiki/William_Adama) to keep old tech, I'm going to at least not be in your way.

Changes:

Generally made SSH_config closer to other updates.
  Added ability to use an IdentityFile (untested).
  ssh_config_actual: Added skipping machine if it is a Windows one (may change if the demand comes up).
  Added understanding if the public ip should be used.
  update-hosts: Moved the bastion decision out of the host creation and made it work the same as other updaters.
  ssh_config_actual: startup.sh: If ssh directive is set, 
    the WSL config is set to include the same cloud-profiler file that "Windows" uses.

Changed internet connectivity checker to both use a DNS (which seems to actually be the issue with WSL) and not only open a socket, but actually obtain some headers from google.
PEP8 stuff.

## v5.2.2 - [Trackss](https://tfwiki.net/wiki/Tracks_(G1)) [Raoul](https://tfwiki.net/wiki/Raoul)
Changes:
The "'" was not a good idea...

## v5.2.1 - [Tracks's](https://tfwiki.net/wiki/Tracks_(G1)) [Raoul](https://tfwiki.net/wiki/Raoul)
Version name thoughts: Raoul can fix anything without even knowing what it is (like a freaking autobot).
Tracks's Raoul: Added checking if the container image matches the expected version.

## v5.2.0 - [Tracks](https://tfwiki.net/wiki/Tracks_(G1))
Version name thoughts: Tracks's main trait is that he's vain... just like this version features.

Changes:

Changing vanity to include the version name (not just the number)

Now checking internet connectivity before trying to issue API calls.

Dependabot upgrade for "urllib3" and "requests".
Updated python base container.

## v5.1.3 -  [Buckbeak](https://harrypotter.fandom.com/wiki/Buckbeak)
Version name thoughts: I've asked Shir for a name for a "mount"... 
  This is what her [Teletraan I](https://tfwiki.net/wiki/Teletraan_I) come up with... Mean anything to you?

Changes:

Corrected mounts (again).

Fixed ssh config adding the wrong location (regression bug).

## v5.1.2 - [Mō-Mō](https://inuyasha.fandom.com/wiki/M%C5%8D-M%C5%8D) 
Fixed mounts again...

## v5.1.1 - [Myōga](https://inuyasha.fandom.com/wiki/My%C5%8Dga)
Fixed incorrect mounts for windows which caused the "reading the repo config file" & "SSH config",
  to not work.

## v5.1.0 - [Ruri'iro Kujaku](https://bleach.fandom.com/wiki/Yumichika_Ayasegawa#Zanpakut.C5.8D)
Added the ability to set color profiles for Moba.

## v5.0.3 - [Hal Roach](https://pixar.fandom.com/wiki/Hal#:~:text=He%20is%20a%20cockroach%20that,EVE%2C%20he%20suffers%20no%20harm.)
Seems I got the "normal start" defined both in the new way and the old in startup.sh. Removed it so it works corecctly.

## v5.0.2 - [Bombshell](https://tfwiki.net/wiki/Bombshell_(G1))
Forgot to move Moba update profile back to main

## v5.0.1 - [Horseshoe Crab](https://havenmaine.fandom.com/wiki/Horseshoe_crab#:~:text=The%20Horseshoe%20Crab%20appearing%20in,one%20following%20her%20in%20Crush.)
Actually, I myself moved back to Windows and couldn't be happier...
Also fixed decency of PyYAML from dependabot.

## v5.0.0 - [Hakuteiken](https://bleach.fandom.com/wiki/Sh%C5%ABkei:_Hakuteiken)
Version name thoughts: Ichigo said: "Sorry, but I don't have any amazing technics like that". 
  This is what this version is... a beautiful white dove of peace that brought me back from MacOS to Windows.

Changes:

Windows WSLv2 support.

Added "Update" profile to Moba created sessions file.

Changed it so that on Windows the "Cloud_Profiler" within documents is used for everything (dot something dir with conf in them is more of a POSIX thing).

Parallelized AWS accounts as well :)

Now filtering the AWS region before even calling the thread that should collect the data.

More outputs now include the instance id (mainly to avoid collisions).


## v4.4.2 - [Shrapnel](https://tfwiki.net/wiki/Shrapnel_(G1))
Fixed a bud, where profiling did not work for non STS users.

## v4.4.1 - [kickback](https://tfwiki.net/wiki/Kickback_(G1))
Corrected Dockerfile for multi-platform.
Added links to version names in the changelog.

## v4.4.0 - [Ephraim](https://www.facebook.com/guy.ephraim) (Deleteing is the best from of coding)
Removed the colors submodule.

Dockerfile improvements to reduce the image size.

Updated the alpine version.

Deleted unused code.

## v4.3.5 - [Saimyōshō](https://inuyasha.fandom.com/wiki/Saimy%C5%8Dsh%C5%8D) (Poison Insects of Hell)
Reverted the change of looking for the tag directive anywhere in the value (introduced in v4.0.1).

This caused too many collisions for the "Name" containing tag values (like Con_username and Bastion_Con_username).

The amount of work that would be required to maintain such a generic value from not colliding with others was deemed to be too great,
and with the potential of affecting too many "legacy" configurations already set on instances.

Also, the advantages of doing this type of "search" were greatly diminished due to clean up work done since that version.

## v4.3.4 - [Shira](https://www.facebook.com/shira.cohen.712) (Not the warrior princess)
Fixed update for "normal" users that don't run Cloud_profiler with root for "Docker context" creation.

## v4.3.3 - [Kōtotsu](https://bleach.fandom.com/wiki/Dangai) (Wresting-Surge)
Startup script cleanups to remove logic of not knowing the version and reduce restarts of container.

## v4.3.2 - [Haien](https://bleach.fandom.com/wiki/Haien) (Abolishing Flames)
Start of removing "master" branch. (It will be maintained for legacy compatibility for now)

## v4.3.1 - [Kakushitsuijaku](https://bleach.fandom.com/wiki/Kakushitsuijaku) (Footprint-Attentive Pursuing-Sparrows)
Seeing that the "Update profile" is the most likely path to become a beta tester,

I've removed the branch selection from the "TL;DR" installer.

## v4.3.0 - [Tenteikūra](https://bleach.fandom.com/wiki/Tenteik%C5%ABra) (Heavenly Rickshaws in Silken Air)
Adding multi arch support!! (M1 mac users, you're welcome).

Moved to 3 digit versioning.

Changed the update profile "file name" to not contain the version for easier upgrades.

## v4.2 - [Kurohitsugi](https://bleach.fandom.com/wiki/Kurohitsugi) (Black Coffin)
Moved to using Alpine as the base image to reduce CVEs.

Removing "sh" from the final form of the container required weaning off GNU usage.

Fixed docker context creation to actually work.

## v4.1.3 - [Nega Scott](https://scottpilgrim.fandom.com/wiki/Nega_Scott)
SSH config - Bastions where not used when they should have been,

## v4.1.2 - [Akuma](https://miraculousladybug.fandom.com/wiki/Akuma)
SSH config - bastions were self looping.

## v4.1.1 - [Cero](https://bleach.fandom.com/wiki/Cero) (Hollow Flash)
Fixed Docker context and SSH config creations (they were still using pre v4.0 methods to access data).

## v4.1 - [Hōrin](https://bleach.fandom.com/wiki/H%C5%8Drin) (Disintegrating Circle)
Added ability to set the SSH command to use from the config file.

Dockerfile: Added OS upgrade to lower CVEs.

Moved where we copy the requirements, 
  so it doesn't invalidate the cache too soon, and it's visually closer to where it is used.

BUG: Corrected the name of the attribute we're looking for in the "script_config".

Added deleting the container if the version has changed (as indicated by the file name).

Reduced linting issues from "startup" script.

Updated README to include instructions about the new "SSH_command" directive, and for better readability.

## v4.0.1 - [Tsuriboshi](https://bleach.fandom.com/wiki/Tsuriboshi) (Suspending Star)
Changed it, so the value of the tag we're looking for, can be anywhere in the tag value we get from AWS.

The tag "dynamic_profile_parent_name" was changed to "dynamic_profile_parent", in order to not collide with the "Name"
tag.

## v4.0 - [Daiyōkai](https://inuyasha.fandom.com/wiki/Daiy%C5%8Dkai) (in a "class" of my own :)
Moved to using a "class" for the machines profiles instead of a nested dict ＼(｀0´)／.

Added "legacy cleaner"/"dynamic profile file versioner", to remove all files that don't match the current version. 

Many linting fixes with the help of [IDEA](https://www.jetbrains.com/?from=https://github.com/aviadra/Cloud-profiler).

Removed the "update_hosts" and "groups" features, that were imported from the original
[gist by gmartinerro](https://gist.github.com/gmartinerro/40831c8874ebb32bc17711af95e1416b). 

## v3.0.3
Traces of the old version leaked in and cause ppl to get the double guid error.

This version is mainly to force the deletion of all update profiles with the issue.

Also, removed the guid from the update profile all together, so this will not happen again.

## v3.0.2 - [How the mighty have fallen](https://en.wiktionary.org/wiki/how_the_mighty_have_fallen) (leaving VScode)
Now actually using threads within the subprocesses and Parallel_exec is no longer used (not even for debugging...
thank you Intellij)

Adjusted changelog to look more like it should (now that I have a builtin preview with intellij) 

## v3.0.1
Parallel_exec bug - This was set to False when I developed and skewed my results :\\

Changed the way we handle the creation of ssh config.

## v3.0 - [Bakusaiga](https://inuyasha.fandom.com/wiki/Bakusaiga)
Started using intellij Pycharm and IDEA.
Switched to using multiprocessing (instead of threads), dramatically improving the execution time,
as processes don't share the boto client connection state.

Fixed all pycharm suggestions for cleaner code.

## v2.0.2
Fixed SSH config directory error for new users that don't have any configuration yet.

## v2.0.1
Fixed windows detection typo

## v2.0 - [Kaze no Kizu](https://inuyasha.fandom.com/wiki/Kaze_no_Kizu)
Added creating docker contexts.

Added preliminary support for creating SSH configs.

Updated superlinter version used.

## v1.8.4
Added the tags "PrivateDnsName" and "ImageId" for AWS instances to be part of the information gathered.

Internal, Added repo linting as Github action.

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

## v1.6.4 - [Bankotsu](https://inuyasha.fandom.com/wiki/Bankotsu)
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

## v1.6 - [Sōryūha](https://inuyasha.fandom.com/wiki/S%C5%8Dry%C5%ABha)
Docker for windows support is now a first class citizen.

Moved to use multi-stage builds.

Fixed STS issue when system user has spaces.

STS assume role exception now gives the actual exception message from boto.

Now syncing container time with NTP before running, due to Windows finicky behavior.

## v1.5.1
Changed Docker base to use "python:slim-buster". This reduced the image size from 1.13G to 392M. \m/ (>_<) \m/

## v1.5 - [Tokijin](https://inuyasha.fandom.com/wiki/T%C5%8Dkijin)
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


## v1.3 - [Bankai](https://bleachfanfiction.fandom.com/wiki/Bankai)
Now supporting running on Windows and creating "MobaXterm" profiles (test on v12.4)

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


## v1.0.1 - [Shikai](https://bleachfanfiction.fandom.com/wiki/Shikai)
Added the ability to block the use of a Bastion, by setting the tag iTerm_bastion to the value of "no".

Corrected DO bug not using Bastion.

Added self-healing for usage of random port by detecting an already established tunnel and killing it before trying to
connect if the variable is already set.

Added ability to run without parallelization (mainly for debugging)