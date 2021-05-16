#!/usr/bin/env bash
[ -z ${CP_Version+x} ] && CP_Version='v4.4.2'
Personal_Static_Profiles="${HOME}/iTerm2-static-profiles"
SRC_Static_Profiles="/home/appuser/iTerm2-static-profiles"
SRC_Docker_image_base="aviadra/cp"
SRC_Docker_Image="${SRC_Docker_image_base}:${CP_Version}"
if grep -qi Microsoft /proc/version 2> /dev/null; then
  WSL="True"
  Base_Path="$( wslpath "$(wslvar USERPROFILE)" )/Documents/Cloud_profiler"
  Config_File="config.yaml"
  Personal_Static_Profiles="${Base_Path}/Static-profiles"
  DynamicProfiles_Location="${Base_Path}/DynamicProfiles"
else
  WSL="False"
  Base_Path="${HOME}"
  Config_File=".iTerm-cloud-profile-generator/config.yaml"
  
  Personal_Static_Profiles="${Base_Path}/iTerm2-static-profiles"
  DynamicProfiles_Location="${HOME}/Library/Application\ Support/iTerm2/DynamicProfiles/"
fi
Personal_Config_File="${Base_Path}/${Config_File}"
if [[ -e ${Personal_Config_File} ]]; then
  Shard_Key_Path="$( cat < "${Personal_Config_File}" | grep SSH_keys_path | awk '{print $2}' | sed -e 's/[[:space:]]//' -e 's/^"//' -e 's/"$//' )"
else
  if [[ ${WSL} == "False" ]]; then
    mkdir -p "${Base_Path}/.iTerm-cloud-profile-generator/keys"
  fi
  Shard_Key_Path="${Base_Path}/keys"
fi


echo "Personal_Config_File: ${Personal_Config_File}"
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
    if [[ ${WSL} == "True" ]]; then
      echo "I have found that in these types of cases, creating a new terminal session is a good idea."
      echo "if that failes, restating the WSL-vm."
      echo -e "To do so, from an elevated PowerShell prompt, issue:\nwsl --shutdown"
      echo "Once that is done, Docker should promot you to restart it. Do it..."
    fi
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
  echo -e "Cloud-profiler - Normal start - Starting service\n"
  echo -e "Cloud-profiler - Normal start - This may take a while....\n"
  if [[ ${WSL} == "False" ]]; then
    UID_FOR_CONTAINER="$(id -u)"
    Dlocation="$( -v "$(eval echo "${DynamicProfiles_Location}:/home/appuser/DynamicProfiles" )" )"
  else
    Dlocation=""
    UID_FOR_CONTAINER=0
  fi
  docker run \
    -u ${UID_FOR_CONTAINER} \
    --init \
    --restart=always \
    -d \
    --log-opt max-size=2m \
    --log-opt max-file=5 \
    --name cloud-profiler \
    -e CP_Service=True \
    -e CP_Windows=${WSL} \
    -v "${HOME}"/.ssh/:/home/appuser/.ssh/ \
    -v "$(eval echo "${Personal_Config_File}:/home/appuser/${Config_File}" )" \
    -v "$(eval echo "${Personal_Static_Profiles}/:${SRC_Static_Profiles}" )" \
    ${Dlocation} \
    -v "$(eval echo "${Shard_Key_Path}:/home/appuser/Shard_Keys" )" \
    ${SRC_Docker_Image} >/dev/null
  exit_state "Start service container"
}

ROOT_docker_start() {
  echo -e "Cloud-profiler - Starting service with ROOT."
  echo -e "Cloud-profiler - NOTE: This that it is starting with ROOT! and mount to the docker socket!\n"
  user_waiter
  docker run \
    -u 0 \
    --init \
    --restart=always \
    -d \
    --log-opt max-size=2m \
    --log-opt max-file=5 \
    --name cloud-profiler \
    -e CP_Service=True \
    -e CP_Windows=${WSL} \
    -v "${HOME}"/.ssh/:/root/.ssh/ \
    -v "$(eval echo "${Personal_Config_File}:/root/${Config_File}" )" \
    -v "$(eval echo "${Personal_Static_Profiles}/:${SRC_Static_Profiles}" )" \
    -v "$(eval echo "${HOME}/${DynamicProfiles_Location}:/root/DynamicProfiles/" )" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(eval echo "${HOME}/.docker/contexts/:/root/.docker/contexts/" )" \
    -v "$(eval echo "${Shard_Key_Path}:/home/appuser/Shard_Keys" )" \
    ${SRC_Docker_Image}
  exit_state "Start service container"
}

update_container() {
  echo -e "Cloud-profiler - Checking for updates"
  echo -e "Cloud-profiler - Update container - This may take a while....\n"
  docker pull ${SRC_Docker_Image}
}

setup() {
  echo "Cloud-profiler - Basic setup parts missing. Will now setup."
  echo "Cloud-profiler - Creating the container to copy profiles and config from."
  echo "Cloud-profiler - Setup - This may take a while...."
  docker rm -f cloud-profiler-copy &> /dev/null

  if [[ ! -e "${DynamicProfiles_Location}" && ${WSL} == "False" ]]; then
    mkdir -p "${DynamicProfiles_Location}" ; exit_state "Create directory ${DynamicProfiles_Location}"
  fi
  if [[ ! -e "${Personal_Static_Profiles}" ]]; then
    mkdir -p "${Personal_Static_Profiles}" ; exit_state "Create directory ${Personal_Static_Profiles}"
  fi
  if [[ ! -e "${Shard_Key_Path}" ]]; then
    mkdir -p "${Shard_Key_Path}" ; exit_state "Create directory ${Shard_Key_Path}"
  fi


  if [[ ! -f ${HOME}/.ssh/config ]]; then
    echo "Cloud-profiler - There was no SSH config, so creating one."
    if [[ ! -d ${HOME}/.ssh/ ]]; then
      mkdir -p "${HOME}"/.ssh/ ; exit_state "Create user's ssh config directory"
    fi
    touch "${HOME}"/.ssh/config ; exit_state "Create user default SSH config file"
  fi
  docker create -it --name cloud-profiler-copy ${SRC_Docker_Image} bash >/dev/null ; exit_state "Create copy container"
  if [[ ! -e $(eval "echo ${Personal_Static_Profiles}" ) ]]; then
    docker cp cloud-profiler-copy:${SRC_Static_Profiles} ${Base_Path} ; exit_state "Copy static profiles from copy container"
    echo -e "Cloud-profiler - We've put a default static profiles directory for you in \"${Personal_Static_Profiles}\"."
  fi
  #Update the iTerm "update profile"
  if [[ ${WSL} == "False" ]]; then
    if [[ "$( grep "${CP_Version}" "${Personal_Static_Profiles}/Update iTerm profiles.json" 2> /dev/null |\
          grep Name |\
          awk -F ":" '{print $2}' |\
          awk -F " " '{print $4}' |\
          tr -d ",",'"' )" != "${CP_Version}" &&\
        ( ${CP_Version} != "edge" && ${CP_Version} != "latest" ) ]]; then
          rm -f "${Personal_Static_Profiles}"/Update* &> /dev/null
          docker cp \
            "$( eval echo "cloud-profiler-copy:${SRC_Static_Profiles}/Update iTerm profiles.json")" \
            "$(eval echo "${Personal_Static_Profiles}" )" ; exit_state "Copy Update profile from copy container"
          echo -e "Cloud-profiler - We've updated the \"Update profile\" in \"${Personal_Static_Profiles}\". It is now at ${CP_Version}"
    fi
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
}

##MAIN

if [[ -z "$( docker images ${SRC_Docker_image_base} | grep -v TAG )" ]] ; then
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

#Is Docker installed on the system?
if [[ -z "$( command -v docker )" ]] ;then
  echo "Cloud-profiler - We can't seem to find docker on the system :\\"
  echo "Cloud-profiler - Make it so the \"which\" command can find it and run gain."
  echo "Cloud-profiler - Goodbye for now..."
  exit 42
fi

# Is a part of the installation missing?
[[ ! -e ${DynamicProfiles_Location} ]] && setup
[[ ! -e ${Personal_Static_Profiles} ]] && setup
[[ ! -e ${Shard_Key_Path} ]] && setup
[[ ! -e ${HOME}/.ssh/config ]] && setup
[[ ! -e $(eval echo "${Personal_Static_Profiles}" ) ]] && setup
[[ ! -e $(eval echo "${Personal_Config_File}" ) ]] && setup
if [[ "$( grep "${CP_Version}"  \
        "${Personal_Static_Profiles}/Update iTerm profiles.json" 2> /dev/null |\
        grep Name |\
        awk -F ":" '{print $2}' |\
        awk -F " " '{print $4}' |\
        tr -d ",",'"' )" != "${CP_Version}" &&\
      ( ${CP_Version} != "edge" && ${CP_Version} != "latest" ) ]] ; then
  clear_service_container
  setup
fi

# Is the correct path for the shared keys set to the desired location?
org_dir="$( pwd )"
desired_keys_dir="$( eval cd "${Shard_Key_Path}" 2> /dev/null;pwd 2> /dev/null )"
current_keys_dir="$( docker inspect cloud-profiler 2> /dev/null \
    | grep "/home/appuser/Shard_Keys" \
    | grep -v Destination \
    | awk -F ':' '{print $1}' \
    | sed -e 's/^[[:space:]]*//' -e 's/^"//' )"
cd "${org_dir}" || exit

# Should we start a Normal or Root container?
if [[ "$( grep -E "^  Docker_contexts_create" "${Personal_Config_File}" | awk '{print $2}' 2>/dev/null )" != "True" ]]; then
  echo "Cloud-profiler - Did not find docker contexts directive"
    if [[ -z "$( docker ps -q -f name=cloud-profiler )" || "${desired_keys_dir}" != "${current_keys_dir}" ]] ; then
      clear_service_container
      Normal_docker_start
    else
      if [[ -z "$(docker ps -q -f name=cloud-profiler)" ]]; then
        Normal_docker_start
      fi
    fi
fi

if [[ "$( grep "^  Docker_contexts_create" "${Personal_Config_File}" | awk '{print $2}' 2> /dev/null )" == "True" ]] ; then
  echo "Cloud-profiler - Found docker contexts directive"
  if [[ -z "$( docker inspect cloud-profiler 2> /dev/null | grep /var/run/docker.sock:/var/run/docker.sock )" || \
        "${desired_keys_dir}" != "${current_keys_dir}" ]] ;then
      clear_service_container
      ROOT_docker_start
  else
      if [[ -z "$(docker ps -q -f name=cloud-profiler)" ]]; then
        ROOT_docker_start
      fi
  fi
fi

# 
if [[ -n "$( docker exec cloud-profiler python3 -c $'import os.path\nif os.path.isfile(\"marker.tmp\"):\n\tprint(\"File exist\")' \
      2> /dev/null )" ]]; then
  echo "Cloud-profiler - There is already a profiles refresh in progress..."
  echo -e "Cloud-profiler - Tailing logs for freshly started container:\n"
  docker logs --since 1.5s -f cloud-profiler 2>&1 | tee >(sed -n "/clouds/ q") | awk '1;/clouds/{exit}'
else
  echo -e "Cloud-profiler - Issuing ad-hoc run."
  docker exec \
    cloud-profiler \
      python3 -c $'import os\nos.mknod("cut.tmp")'
  echo -e "Cloud-profiler - Tailing logs for already running container:\n"
  docker logs --since 1.5s -f cloud-profiler 2>&1 | tee >(sed -n "/clouds/ q")| awk '/Start of loop/,/clouds/'
  echo -e "Cloud-profiler - Tailing logs DONE.\n"
fi

docker ps -f name=cloud-profiler ; exit_state "Finding the service profile in docker ps"
