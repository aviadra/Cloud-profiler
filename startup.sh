#!/usr/bin/env bash
Personal_Static_Profiles="~/iTerm2-static-profiles"
Config_File=".iTerm-cloud-profile-generator/config.yaml"
Personal_Config_File="~/${Config_File}"
SRC_Static_Profiles="/home/appuser/iTerm2-static-profiles"
DynamicProfiles_Location="Library/Application\ Support/iTerm2/DynamicProfiles/"
SRC_Docker_Image="aviadra/cp:${CP_Version}"

[ -z ${CP_Version+x} ] && CP_Version='latest'
if [[ ! -e $(eval echo ${Personal_Static_Profiles} ) || ! -e $(eval echo ${Personal_Config_File} ) ]]; then
    echo 1
    docker create -it --name cloud-profiler-copy ${SRC_Docker_Image} bash
    if [[ ! -e $(eval echo ${Personal_Static_Profiles} ) ]]; then
        docker cp cloud-profiler-copy:${SRC_Static_Profiles} ~/
        echo -e "We've put a default static profiles directory for you in \"${Personal_Static_Profiles}\"."
    fi
    if [[ ! -e $(eval echo ${Personal_Config_File} ) ]]; then
        mkdir -p "$(eval dirname ${Personal_Config_File})"
        docker cp cloud-profiler-copy:/home/appuser/config.yaml "$(eval echo ${Personal_Config_File})"
        echo -e "We've put a default configuration file for you in \"${Personal_Config_File}\".\nPlease edit it to set your credentials and preferences"
    fi
    docker rm -f cloud-profiler-copy
else
    echo 4
    if [[ -z "$(docker ps -q -f name=cloud-profiler)" ]]; then
        echo 5
        echo "Starting Cloud-profiler service\n"
        docker run \
            --init \
            --restart=always \
            -d \
            --name cloud-profiler \
            -e CP_Service=True \
            -v "$(eval echo ${Personal_Config_File}:/home/appuser/${Config_File} )" \
            -v "$(eval echo ${Personal_Static_Profiles}/:${SRC_Static_Profiles} )" \
            -v "$(eval echo ~/${DynamicProfiles_Location}:/home/appuser/${DynamicProfiles_Location} )" \
            ${SRC_Docker_Image}
    else
        echo 6
        echo -e "Cloud-profiler service already running\n"
    fi
    docker ps -f name=cloud-profiler
fi