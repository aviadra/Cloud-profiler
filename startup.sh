#!/usr/bin/env zsh
[ -z ${CP_Version+x} ] && CP_Version='latest'
CP_Update_Profile_VERSION="v1.7.3"
Personal_Static_Profiles="~/iTerm2-static-profiles"
Config_File=".iTerm-cloud-profile-generator/config.yaml"
Personal_Config_File="~/${Config_File}"
SRC_Static_Profiles="/home/appuser/iTerm2-static-profiles"
DynamicProfiles_Location="Library/Application\ Support/iTerm2/DynamicProfiles/"
SRC_Docker_image_base="aviadra/cp"
SRC_Docker_Image="${SRC_Docker_image_base}:${CP_Version}"

Normal_docker_start() {
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
}

if [[ ! -e $(eval echo ${Personal_Static_Profiles} ) || \
      ! -e $(eval echo ${Personal_Config_File} ) || \
      ! -e "${Personal_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json" ]]
then
    docker rm -f cloud-profiler-copy &> /dev/null
    docker create -it --name cloud-profiler-copy ${SRC_Docker_Image} bash
    if [[ ! -e $(eval echo ${Personal_Static_Profiles} ) ]]; then
        docker cp cloud-profiler-copy:${SRC_Static_Profiles} ~/
        echo -e "We've put a default static profiles directory for you in \"${Personal_Static_Profiles}\"."
    fi
    if [[ ! -e "$( eval echo ${Personal_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json )" ]]; then
        rm -f "$( eval echo "${Personal_Static_Profiles}/Update*" )"
        docker cp "$( eval echo "cloud-profiler-copy:${SRC_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json")" "$(eval echo ${Personal_Static_Profiles})"
        echo -e "We've updated the \"Update proflile\" in \"${Personal_Static_Profiles}\". It is now at ${CP_Update_Profile_VERSION}"
    fi
    if [[ ! -e $(eval echo ${Personal_Config_File} ) ]]; then
        mkdir -p "$(eval dirname ${Personal_Config_File})"
        docker cp cloud-profiler-copy:/home/appuser/config.yaml "$(eval echo ${Personal_Config_File})"
        echo -e "We've put a default configuration file for you in \"${Personal_Config_File}\"."
        echo -e "\nPlease edit it to set your credentials and preferences"
        exit 0
    fi
    docker rm -f cloud-profiler-copy &> /dev/null
fi
if [[ -z "$(docker ps -q -f name=cloud-profiler)" ]]; then
    echo "Starting Cloud-profiler service\n"
    Normal_docker_start
else
    echo -e "Cloud-profiler service already running\n"
    echo -e "Checking for updates\n"
    on_system_digests=$(docker images --digests | grep ${SRC_Docker_image_base} | grep $CP_Version | awk '{print $3}')
    latest_version_raw=$( docker pull ${SRC_Docker_Image})
    latest_version_digets="$( echo $latest_version_raw | grep Digest | awk '{print $2}' )"
    if [[ "${latest_version_digets}" != "${on_system_digests}" ]]; then
      echo -e "Newer version of container detected.\n"
      echo -e "Now restarting service for changes to take affect."
      docker stop cloud-profiler
      docker rm cloud-profiler
      Normal_docker_start
    else
        echo -e "Issuing ad-hoc run."
        docker exec \
            cloud-profiler \
            python3 update-cloud-hosts.py
    fi
fi
docker ps -f name=cloud-profiler
