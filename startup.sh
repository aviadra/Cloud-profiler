#!/usr/bin/env bash
[ -z ${CP_Version+x} ] && CP_Version='v4.3.2'
Personal_Static_Profiles="${HOME}/iTerm2-static-profiles"
Config_File=".iTerm-cloud-profile-generator/config.yaml"
Personal_Config_File="${HOME}/${Config_File}"
SRC_Static_Profiles="/home/appuser/iTerm2-static-profiles"
SRC_Docker_image_base="aviadra/cp"
SRC_Docker_Image="${SRC_Docker_image_base}:${CP_Version}"
update_detected="no"
check_for_updates="true"
DynamicProfiles_Location="Library/Application\ Support/iTerm2/DynamicProfiles/"
if [[ -e ${HOME}/${Config_File} ]]; then
  Shard_Key_Path="$( cat < "${HOME}/${Config_File}" | grep SSH_keys_path | awk '{print $2}' | sed -e 's/^"//' -e 's/"$//' )"
else
  mkdir -p "${HOME}/.iTerm-cloud-profile-generator/keys"
  Shard_Key_Path="${HOME}/keys"
fi

echo -e "Cloud-profiler - Welcome to the startup/setup script."

user_waiter() {
  echo -e "Cloud-profiler - If this is not what you wish to do, CTRL+C to abort."
  BAR='##################################################'   # this is full bar, e.g. 20 chars
  for i in {1..50}; do
    echo -ne "\r${BAR:0:$i}" # print $i chars of $BAR from 0 position
    sleep .1                 # wait 100ms between "frames"
  done
  echo -e "\n"
}

exit_state() {
  # shellcheck disable=SC2181
  if [[ $? != 0 ]]; then
    echo "Cloud-profiler - Something went wrong with \"$1\"..."
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
  echo -e "Cloud-profiler - This may take a while....\n"
  clear_service_container
  docker run \
    --init \
    --restart=always \
    -d \
    --log-opt max-size=2m \
    --log-opt max-file=5 \
    --name cloud-profiler \
    -e CP_Service=True \
    -v "${HOME}"/.ssh/:/home/appuser/.ssh/ \
    -v "$(eval echo "${Personal_Config_File}:/home/appuser/${Config_File}" )" \
    -v "$(eval echo "${Personal_Static_Profiles}/:${SRC_Static_Profiles}" )" \
    -v "$(eval echo "${HOME}/${DynamicProfiles_Location}:/home/appuser/${DynamicProfiles_Location}" )" \
    -v "$(eval echo "${Shard_Key_Path}:/home/appuser/Shard_Keys" )" \
    ${SRC_Docker_Image}
  exit_state "Start service container"
}

ROOT_docker_start() {
  echo -e "Cloud-profiler - Starting service."
  echo -e "Cloud-profiler - NOTE: This that it is starting with ROOT! and mount to the docker socket!\n"
  user_waiter
  echo -e "Cloud-profiler - This may take a while....\n"
  clear_service_container
  docker run \
    -u 0 \
    --init \
    --restart=always \
    -d \
    --log-opt max-size=2m \
    --log-opt max-file=5 \
    --name cloud-profiler \
    -e CP_Service=True \
    -v "${HOME}"/.ssh/:/root/.ssh/ \
    -v "$(eval echo "${Personal_Config_File}:/root/${Config_File}" )" \
    -v "$(eval echo "${Personal_Static_Profiles}/:${SRC_Static_Profiles}" )" \
    -v "$(eval echo "${HOME}/${DynamicProfiles_Location}:/root/${DynamicProfiles_Location}" )" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(eval echo "${HOME}/.docker/contexts/:/root/.docker/contexts/" )" \
    -v "$(eval echo "${Shard_Key_Path}:/home/appuser/Shard_Keys" )" \
    ${SRC_Docker_Image}
  exit_state "Start service container"
}

update_container() {
  echo -e "Cloud-profiler - Checking for updates"
  echo -e "Cloud-profiler - This may take a while....\n"
  on_system_digests=$(docker images --digests | grep ${SRC_Docker_image_base} | grep $CP_Version | awk '{print $3}')
  docker pull ${SRC_Docker_Image}
  latest_version_digits=$( docker pull ${SRC_Docker_Image} | grep Digest | awk '{print $2}' )
  if [[ "${latest_version_digits}" != "${on_system_digests}" ]]; then
    echo -e "Cloud-profiler - Newer version of container detected.\n"
    echo -e "Cloud-profiler - Now restarting service for changes to take affect."
    update_detected="yes"
  fi
}

setup() {
  [[ ${check_for_updates} == "true" ]] && update_container
  if [[ ${CP_Version} == "edge" ||\
        ${CP_Version} == "latest" ]]; then
      CONSIDER_VERSION="NO"
  else
      CONSIDER_VERSION="YES"
  fi
  if [[ ! -e $(eval echo "${Personal_Static_Profiles}" ) || \
    ! -e $(eval echo "${Personal_Config_File}" ) || \
    ! -f ${HOME}/.ssh/config || \
    ! -e "${HOME}/iTerm2-static-profiles/Update\ iTerm\ profiles.json" ||\
     ( "$( grep "${CP_Version}"  \
        ${HOME}/iTerm2-static-profiles/Update\ iTerm\ profiles.json |\
        grep Name |\
        awk -F ":" '{print $2}' |\
        awk -F " " '{print $4}' |\
        tr -d ",",'"' )" != "${CP_Version}" && $CONSIDER_VERSION == "YES") ]]; then

    echo "Cloud-profiler - Basic setup parts missing. Will now setup."
    echo "Cloud-profiler - Creating the container to copy profiles and config from."
    echo "Cloud-profiler - This may take a while...."
    docker rm -f cloud-profiler-copy &> /dev/null

    if [[ ! -f ${HOME}/.ssh/config ]]; then
      echo "Cloud-profiler - There was no SSH config, so creating one"
      if [[ ! -d ${HOME}/.ssh/ ]]; then
        mkdir -p "${HOME}"/.ssh/ ; exit_state "Create user's ssh config directory"
      fi
      touch "${HOME}"/.ssh/config ; exit_state "Create user default SSH config file"
    fi
    docker create -it --name cloud-profiler-copy ${SRC_Docker_Image} bash &> /dev/null ; exit_state "Create copy container"
    if [[ ! -e $(eval "echo ${Personal_Static_Profiles}" ) ]]; then
      docker cp cloud-profiler-copy:${SRC_Static_Profiles} ~/ ; exit_state "Copy static profiles from copy container"
      echo -e "Cloud-profiler - We've put a default static profiles directory for you in \"${Personal_Static_Profiles}\"."
    fi
    if [[ "$( grep "${CP_Version}"  \
      ${HOME}/iTerm2-static-profiles/Update\ iTerm\ profiles.json |\
        grep Name |\
        awk -F ":" '{print $2}' |\
        awk -F " " '{print $4}' |\
        tr -d ",",'"' )" != "${CP_Version}" && $CONSIDER_VERSION == "YES" ]]; then
        rm -f "${Personal_Static_Profiles}"/Update* &> /dev/null
        docker cp \
          "$( eval echo "cloud-profiler-copy:${SRC_Static_Profiles}/Update iTerm profiles.json")" \
          "$(eval echo "${Personal_Static_Profiles}" )" ; exit_state "Copy Update profile from copy container"
        echo -e "Cloud-profiler - We've updated the \"Update profile\" in \"${Personal_Static_Profiles}\". It is now at ${CP_Version}"
    fi
    if [[ ! -e $(eval "echo ${Personal_Config_File}" ) ]]; then
      mkdir -p "$(eval dirname "${Personal_Config_File}" )" ; exit_state "Create personal config dir"
      docker cp cloud-profiler-copy:/home/appuser/config.yaml "$(eval echo "${Personal_Config_File}" )"
      exit_state "Copy personal config template from copy container"
      echo -e "Cloud-profiler - We've put a default configuration file for you in \"${Personal_Config_File}\"."
      echo -e "\nCloud-profiler - Please edit it to set your credentials and preferences"
      exit 0
    fi
    docker rm -f cloud-profiler-copy &> /dev/null ; exit_state "Delete copy container"
  fi
  Normal_docker_start
}

##MAIN

if [[ -z "$(docker images --digests | grep ${SRC_Docker_image_base} | grep $CP_Version | awk '{print $3}')" ]] ; then
  echo -e "Cloud-profiler - This script will install the \"Cloud Profiler\" service using a docker container."
  user_waiter
fi

#Legacy cleaner

for f in ${HOME}/iTerm2-static-profiles/Update\ iTerm\ profiles?*.json; do

    if [ -e "$f" ]; then
      echo -e "Cloud-profiler - Legacy update profile file found:"
      echo -e "Cloud-profiler - $f."
      echo -e "Cloud-profiler - Deleteing..."
      rm -f "${f}"
    else
      echo "Cloud-profiler - Legacy files not found"
    fi
    break
  done

if [[ -z "$(command -v docker)" ]] ;then
  echo "Cloud-profiler - We can't seem to find docker on the system :\\"
  echo "Cloud-profiler - Make it so the \"which\" command can find it and run gain."
  echo "Cloud-profiler - Goodbye for now..."
  exit 42
fi

[[ ! -e ${HOME}/.ssh/config ]] && setup
[[ ! -e $(eval echo "${Personal_Static_Profiles}" ) ]] && setup
[[ ! -e $(eval echo "${Personal_Config_File}" ) ]] && setup
if [[ ! -e "$(eval echo "${Personal_Static_Profiles}/Update iTerm profiles ${CP_Version}.json")" ]];then
  clear_service_container
  setup
fi

org_dir="$( pwd )"
desired_keys_dir="$( eval cd "${Shard_Key_Path}";pwd )"
current_keys_dir="$( docker inspect cloud-profiler \
    | grep "/home/appuser/Shard_Keys" \
    | grep -v Destination \
    | awk -F ':' '{print $1}' \
    | sed -e 's/^[[:space:]]*//' -e 's/^"//' )"
cd "${org_dir}" || exit

[[ ( "$( cat < "${Personal_Config_File}" | \
          grep -E "^  Docker_contexts_create" | \
          awk '{print$2}' 2>/dev/null )" != "true" && \
      -z "$(docker ps -q -f name=cloud-profiler)" ) || \
     "${desired_keys_dir}" != "${current_keys_dir}" ]] && \
Normal_docker_start

if [[ "$( cat < "${Personal_Config_File}" | grep "^  Docker_contexts_create" | awk '{print$2}' 2> /dev/null )" == "True" ]] ; then
  echo "Cloud-profiler - Found docker contexts directive"
    if [[ -z "$(docker ps -q -f name=cloud-profiler)" || \
          -z "$( docker inspect cloud-profiler | grep /var/run/docker.sock:/var/run/docker.sock 2> /dev/null )" || \
          "${desired_keys_dir}" != "${current_keys_dir}" ]] ;then
          ROOT_docker_start
    fi
fi
if [[ -n "$(docker ps -q -f name=cloud-profiler)" ]]; then
  echo -e "Cloud-profiler - Service already running\n"
  if [[ -n "$( docker exec cloud-profiler python3 -c $'import os.path\nif os.path.isfile(\"marker.tmp\"):\n\tprint(\"File exist\")' 2> /dev/null )" ]]
  then
    echo "Cloud-profiler - There is already a profiles refresh in progress..."
    echo -e "Cloud-profiler - Tailing logs for freshly started container:\n"
    docker logs --since 1.5s -f cloud-profiler 2>&1 |tee >(sed -n "/clouds/ q") | awk '1;/clouds/{exit}'
  else
    echo -e "Cloud-profiler - Issuing ad-hoc run."
    docker exec \
      cloud-profiler \
        python3 -c $'import os\nos.mknod("cut.tmp")'
    echo -e "Cloud-profiler - Tailing logs for already running container:\n"
    docker logs --since 1.5s -f cloud-profiler 2>&1 | tee >(sed -n "/clouds/ q")| awk '/Start of loop/,/clouds/'
    echo -e "Cloud-profiler - Tailing logs DONE.\n"
  fi
  [[ ${check_for_updates} == "true" ]] && update_container
  [[ "${update_detected}" == "yes" ]] && Normal_docker_start
fi
docker ps -f name=cloud-profiler ; exit_state "Finding the service profile in docker ps"
