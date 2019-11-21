# Change Log

## v1.0.1
Added the ability to block the use of a bastion, by setting the tag iTerm_bastion to the value of "no".
Corrected DO bug not using Bastion.
Added self healing for usage of random port by detecting an already established tunnel and killing it before trying to connect if the variable is already set.
Added ability to run without parallelizationly (mainly for debugging)