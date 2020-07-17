#!/usr/bin/env bash
[ -z ${CP_Version+x} ] && CP_Version='latest'
CP_Update_Profile_VERSION="v1.8.4"
Personal_Static_Profiles="${HOME}/iTerm2-static-profiles"
Config_File=".iTerm-cloud-profile-generator/config.yaml"
Personal_Config_File="${HOME}/${Config_File}"
SRC_Static_Profiles="/home/appuser/iTerm2-static-profiles"
DynamicProfiles_Location="Library/Application\ Support/iTerm2/DynamicProfiles/"
SRC_Docker_image_base="aviadra/cp"
SRC_Docker_Image="${SRC_Docker_image_base}:${CP_Version}"
update_detected="no"

echo -e "Cloud-profiler - Welcome to the startup/setup script."

exit_state() {
    # shellcheck disable=SC2181
    if [[ $? != 0 ]]; then
        echo "Cloud-profiler - Something when wrong with \"$1\"..."
        echo "Aborting."
        docker rm -f cloud-profiler-copy &> /dev/null
        exit 42
    fi
}

clear_service_container() {
    docker stop cloud-profiler &> /dev/null
    docker rm cloud-profiler &> /dev/null
}

Normal_docker_start() {
    echo -e "Cloud-profiler - Starting service\n"
    clear_service_container
    docker run \
        --init \
        --restart=always \
        -d \
        --log-opt max-size=2m \
        --log-opt max-file=5 \
        --name cloud-profiler \
        -e CP_Service=True \
        -v "$(eval echo "${Personal_Config_File}:/home/appuser/${Config_File}" )" \
        -v "$(eval echo "${Personal_Static_Profiles}/:${SRC_Static_Profiles}" )" \
        -v "$(eval echo "${HOME}/${DynamicProfiles_Location}:/home/appuser/${DynamicProfiles_Location}" )" \
        ${SRC_Docker_Image} &> /dev/null
    exit_state "Start service container"
}

update_container() {
    echo -e "Cloud-profiler - Checking for updates"
    echo -e "Cloud-profiler - This may take a while....\n"
    on_system_digests=$(docker images --digests | grep ${SRC_Docker_image_base} | grep $CP_Version | awk '{print $3}')
    latest_version_digets=$( docker pull ${SRC_Docker_Image} | grep Digest | awk '{print $2}' )
    if [[ "${latest_version_digets}" != "${on_system_digests}" ]]; then
      echo -e "Cloud-profiler - Newer version of container detected.\n"
      echo -e "Cloud-profiler - Now restarting service for changes to take affect."
      update_detected="yes"
    fi
}

setup() {
    update_container
    if [[ ! -e $(eval echo "${Personal_Static_Profiles}" ) || \
        ! -e $(eval echo "${Personal_Config_File}" ) || \
        ! -e "$( eval echo "${Personal_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json" )" ]] ; then
        
        echo "Cloud-profiler - Besic setup parts missing. Will now setup."
        echo "Cloud-profiler - Creating the container to copy profiles and config from."
        echo "Cloud-profiler - This may take a while...."
        docker rm -f cloud-profiler-copy &> /dev/null
        
        docker create -it --name cloud-profiler-copy ${SRC_Docker_Image} bash &> /dev/null ; exit_state "Create copy container"
        if [[ ! -e $(eval "echo ${Personal_Static_Profiles}" ) ]]; then
            docker cp cloud-profiler-copy:${SRC_Static_Profiles} ~/ ; exit_state "Copy static profiles from copy container"
            echo -e "Cloud-profiler - We've put a default static profiles directory for you in \"${Personal_Static_Profiles}\"."
        fi
        if [[ ! -e "$( eval echo "${Personal_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json" )" ]]; then
            rm -f "${Personal_Static_Profiles}"/Update* &> /dev/null
            docker cp "$( eval echo "cloud-profiler-copy:${SRC_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json")" \
                    "$(eval echo "${Personal_Static_Profiles}" )" ; exit_state "Copy Update profile from copy container"
            echo -e "Cloud-profiler - We've updated the \"Update proflile\" in \"${Personal_Static_Profiles}\". It is now at ${CP_Update_Profile_VERSION}"
        fi
        if [[ ! -e $(eval "echo ${Personal_Config_File}" ) ]]; then
            mkdir -p "$(eval dirname "${Personal_Config_File}" )" ; exit_state "Create personal config dir"
            docker cp cloud-profiler-copy:/home/appuser/config.yaml "$(eval echo "${Personal_Config_File}" )" ; exit_state "Copy personal config template from copy container"
            echo -e "Cloud-profiler - We've put a default configuration file for you in \"${Personal_Config_File}\"."
            echo -e "\nCloud-profiler - Please edit it to set your credentials and preferences"
            exit 0
        fi
        docker rm -f cloud-profiler-copy &> /dev/null ; exit_state "Delete copy container"
    fi
    Normal_docker_start
}

if [[ -z "$(which docker)" ]] ;then
    echo "Cloud-profiler - We can't seem to find docker on the system :\\"
    echo "Cloud-profiler - Make it so the \"which\" command can find it and run gain."
    echo "Cloud-profiler - Goodbye for now..."
    exit 42
fi

[[ ! -e $(eval echo "${Personal_Static_Profiles}" ) ]] && setup
[[ ! -e $(eval echo "${Personal_Config_File}" ) ]] && setup
[[ ! -e "$( eval echo "${Personal_Static_Profiles}/Update iTerm profiles ${CP_Update_Profile_VERSION}.json" )" ]] && setup

if [[ -z "$(docker ps -q -f name=cloud-profiler)" ]]; then
    Normal_docker_start
else
    echo -e "Cloud-profiler - Service already running\n"
    if [[ -n "$( docker exec cloud-profiler ls marker.tmp 2> /dev/null )" ]] ; then
        echo "Cloud-profiler - There is already a profiles refresh in progress..."
        docker logs --since 0.5s -f cloud-profiler 2>&1 |tee >(sed -n "/clouds/ q") | awk '1;/clouds/{exit}'
    else
        echo -e "Cloud-profiler - Issuing ad-hoc run."
        docker exec \
            cloud-profiler \
            touch cut.tmp ; exit_state "ad-hoc run"
        docker logs --since 0.5s -f cloud-profiler 2>&1 | tee >(sed -n "/clouds/ q")| awk '/reset/,/clouds/'
    fi
    update_container
    [[ "${update_detected}" == "yes" ]] && Normal_docker_start
fi
docker ps -f name=cloud-profiler ; exit_state "Finding the service profile in docker ps"
