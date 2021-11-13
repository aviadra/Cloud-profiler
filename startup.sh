#!/usr/bin/env bash
logger()
{
  echo -e "Cloud-profiler - $1"
}
[ -z ${CP_Version+x} ] && CP_Version='v6.1.1_Chasey_Pencive_Flitterby'
[ "${CP_Branch}" == "develop" ] && CP_Version='edge'
Personal_Static_Profiles="${HOME}/iTerm2-static-profiles"
SRC_Static_Profiles="/home/appuser/iTerm2-static-profiles"
SRC_Docker_image_base="aviadra/cp"
SRC_Docker_Image="${SRC_Docker_image_base}:${CP_Version}"
if grep -qi Microsoft /proc/version 2> /dev/null; then
  WSL="True"
  Base_Path="$( powershell.exe -Command '[Environment]::GetFolderPath([Environment+SpecialFolder]::MyDocuments)' )"
  logger "Base_Path: $Base_Path"
  arrIN=(${Base_Path//:/ })
  Base_Path="/mnt/$( echo ${arrIN[0]} | tr '[:upper:]' '[:lower:]' | tr -d '\r' )$( echo ${arrIN[1]} | tr '\\\\' '/' | tr -d '\r' )"
  CP_Path="${Base_Path}/Cloud_profiler"
  logger "Base_Path: $Base_Path"
  Config_File="config.yaml"
  Personal_Static_Profiles="${CP_Path}/Static-profiles"
  DynamicProfiles_Location="${CP_Path}/DynamicProfiles"
else
  WSL="False"
  CP_Path="${HOME}"
  Config_File=".iTerm-cloud-profile-generator/config.yaml"
  Personal_Static_Profiles="${CP_Path}/iTerm2-static-profiles"
  DynamicProfiles_Location="/Library/Application\ Support/iTerm2/DynamicProfiles/"
fi
Personal_Config_File="${CP_Path}/${Config_File}"
if [[ -d ${Personal_Config_File} ]]; then
  logger "Your config \"file\" seems to be a directory..."
  logger "The location is:"
  logger "${Personal_Config_File}"
  logger "Unfortunately, this usually means there was an issue with your setup."
  logger "Fix this and come back…"
  logger "Aborting hard."
  exit 42
fi
if [[ -f ${Personal_Config_File} ]]; then
  Shard_Key_Path="$( cat < "${Personal_Config_File}" | grep SSH_keys_path | awk '{print $2}' | sed -e 's/[[:space:]]//' -e 's/^"//' -e 's/"$//' )"
  SSH_Config_create="$( cat < "${Personal_Config_File}" | grep SSH_Config_create | awk '{print $2}' | sed -e 's/[[:space:]]//' -e 's/^"//' -e 's/"$//' )"
else
  if [[ ${WSL} == "False" ]]; then
    mkdir -p "${CP_Path}/.iTerm-cloud-profile-generator/keys"
  fi
  Shard_Key_Path="${CP_Path}/keys"
fi


logger "Welcome to the startup/setup script."
logger "Personal_Config_File: ${Personal_Config_File}"
user_waiter() {
  logger "If this is not what you wish to do, CTRL+C to abort."
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
    logger "Something went wrong with \"$1\"..."
    if [[ ${WSL} == "True" ]]; then
      echo "I have found that in these types of cases, creating a new terminal session is a good idea."
      echo "If that failes, restat the WSL-vm."
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
  logger "Normal start - Starting service\n"
  logger "Normal start - This may take a while....\n"
  if [[ ${WSL} == "False" ]]; then
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
  else
    Dlocation="$( echo -v "$( eval echo "${CP_Path}:/home/appuser/Documents/Cloud_Profiler" )" )"
    UID_FOR_CONTAINER=0
    docker run \
    -u ${UID_FOR_CONTAINER} \
    --init \
    --restart=always \
    -d \
    --log-opt max-size=2m \
    --log-opt max-file=5 \
    --name cloud-profiler \
    -e CP_OutputDir='/home/appuser/Documents/Cloud_Profiler' \
    -e CP_Service=True \
    -e CP_Windows=${WSL} \
    -v "$( eval echo "${Base_Path}" )/.ssh":/home/appuser/.ssh/ \
    -v "$( eval echo "${Personal_Config_File}:/root/Documents/Cloud_Profiler/${Config_File}" )" \
    -v "$( eval echo "${Personal_Static_Profiles}/:${SRC_Static_Profiles}" )" \
    ${Dlocation} \
    -v "$( eval echo "${Shard_Key_Path}:/home/appuser/Shard_Keys" )" \
    ${SRC_Docker_Image} >/dev/null
  exit_state "Start service container"
  fi  
}

ROOT_docker_start() {
  logger "Starting service with ROOT."
  logger "NOTE: This that it is starting with ROOT! and mount to the docker socket!\n"
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
  logger "Checking for updates."
  logger "Update container - This may take a while....\n"
  docker pull ${SRC_Docker_Image}
}

setup() {
  logger "Setup - Called by \"$1\""
  logger "Setup - This may take a while...."
  docker rm -f cloud-profiler-copy &> /dev/null
  [[ -z "$( docker ps --filter ancestor=${SRC_Docker_Image} -q )" ]] && clear_service_container && update_container
  if [[ ${WSL} == "False" && ! -e "${HOME}/${DynamicProfiles_Location}" ]]; then
    mkdir -p "${HOME}/${DynamicProfiles_Location}" ; exit_state "Create directory ${HOME}/${DynamicProfiles_Location}"
  fi
  if [[ ! -e "${Shard_Key_Path}" ]]; then
    mkdir -p "${Shard_Key_Path}" ; exit_state "Create directory ${Shard_Key_Path}"
  fi
  if [[ ${WSL} == "True" && -z "$( grep "Include $( eval echo $( wslpath $(wslvar USERPROFILE) ) )/.ssh/cloud-profiler" ~/.ssh/config )" \
    && ${SSH_Config_create} == "True" ]]; 
  then
      logger "Setup - Prepending \"include $( wslpath "$(wslvar USERPROFILE)" )/.ssh/cloud-profiler\", to \"~/.ssh/config\""
      echo -e "Include $( wslpath "$(wslvar USERPROFILE)" )/.ssh/cloud-profiler\n$(cat ~/.ssh/config)" > ~/.ssh/config
  fi
  if [[ ! -f ${HOME}/.ssh/config ]]; then
    logger "There was no SSH config, so creating one."
    if [[ ! -d ${HOME}/.ssh/ ]]; then
      mkdir -p "${HOME}"/.ssh/ ; exit_state "Create user's ssh config directory"
    fi
    touch "${HOME}"/.ssh/config ; exit_state "Create user default SSH config file"
  fi
  docker rm -f cloud-profiler-copy
  docker create --name cloud-profiler-copy ${SRC_Docker_Image} bash >/dev/null ; exit_state "Create copy container"
  if [[ ! -e $(eval "echo ${Personal_Static_Profiles}" ) ]]; then
    mkdir -p "${Personal_Static_Profiles}" ; exit_state "Create directory ${Personal_Static_Profiles}"
    echo "SRC_Static_Profiles: ${SRC_Static_Profiles}"
    echo "CP_Path: ${CP_Path}"
    docker cp cloud-profiler-copy:${SRC_Static_Profiles} ${CP_Path} ; exit_state "Copy static profiles from copy container"
    logger "We've put a default static profiles directory for you in \"${Personal_Static_Profiles}\"."
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
          logger "We've updated the \"Update profile\" in \"${Personal_Static_Profiles}\". It is now at ${CP_Version}"
    fi
  fi
  if [[ ! -e $(eval "echo ${Personal_Config_File}" ) ]]; then
    mkdir -p "$(eval dirname "${Personal_Config_File}" )" ; exit_state "Create personal config dir"
    docker cp cloud-profiler-copy:/home/appuser/config.yaml "$( eval echo "${Personal_Config_File}" )"
    exit_state "Copy personal config template from copy container"
    logger "We've put a default configuration file for you in \"${Personal_Config_File}\"."
    echo -e "\nCloud-profiler - Please edit it to set your credentials and preferences"
    exit 0
  fi
  docker rm -f cloud-profiler-copy &> /dev/null ; exit_state "Delete copy container"
}

##MAIN

#Is Docker installed on the system?
if [[ -z "$( command -v docker 2>/dev/null )" ]]; then
  logger "We can't seem to find docker on the system :\\"
  logger "Make it so the \"which\" command can find it and run gain."
  logger "Goodbye for now..."
  exit 42
fi
#Is it working enough to even attempt a pass?
if [[ $( docker images ) ]]; then
  logger "Seems to be running, so continuing."
else
  logger "Was unable to query what images are on the system..."
  logger "Make sure Docker is running"
  logger "Goodbye for now..."
  exit 42
fi

if [[ ${WSL} == "True" && -z "$( wslvar USERPROFILE )" ]]; then
  logger "This terminal session is corrupted."
  logger "Open a new one and try again."
  logger "Goodbye for now..."
  exit 42
fi
if [[ -z "$( docker images ${SRC_Docker_image_base} | grep -v TAG )" ]] ; then
  logger "This script will install the \"Cloud Profiler\" service using a docker container."
  user_waiter
fi

#Legacy cleaner
for f in ${HOME}/iTerm2-static-profiles/Update\ iTerm\ profiles?*.json; do
    if [ -e "$f" ]; then
      logger "Legacy update profile file found:"
      logger "$f."
      logger "Deleteing..."
      rm -f "${f}"
    else
      logger "Legacy files not found"
    fi
    break
  done

# Is a part of the installation missing?
[[ ${WSL} == "True" && -z "$( grep "Include $( eval echo $( wslpath $(wslvar USERPROFILE) ) )/.ssh/cloud-profiler" ~/.ssh/config )" \
  && ${SSH_Config_create} == "True" ]] && setup "SSH config includer"
[[ -z "$( docker ps --filter ancestor=${SRC_Docker_Image} -q )" ]] && setup "looking for \"${SRC_Docker_Image}\" triggered image version changed"
[[ ${WSL} == "False" && ! -e ${HOME}/${DynamicProfiles_Location} ]] && setup 'DynamicProfiles_Location'
[[ ! -e ${Shard_Key_Path} ]] && setup 'Shard_Key_Path'
[[ ! -e ${HOME}/.ssh/config ]] && setup '${HOME}/.ssh/config'
[[ ! -e $(eval echo "${Personal_Static_Profiles}" ) ]] && setup 'Personal_Static_Profiles'
[[ ! -e $(eval echo "${Personal_Config_File}" ) ]] && setup 'Personal_Config_File'
if [[ "$( grep "${CP_Version}"  \
        "${Personal_Static_Profiles}/Update iTerm profiles.json" 2> /dev/null |\
        grep Name |\
        awk -F ":" '{print $2}' |\
        awk -F " " '{print $4}' |\
        tr -d ",",'"' )" != "${CP_Version}" &&\
      ( ${CP_Version} != "edge" && ${CP_Version} != "latest" ) && ${WSL} == "False" ]] ; then
  clear_service_container
  setup 'CP_Version'
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
  logger "Did not find docker contexts directive"
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
  logger "Found docker contexts directive"
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
if [[ -n "$( docker exec cloud-profiler python3 -c $'import os.path\nif os.path.isfile(\"marker.tmp\"):\n\tprint(\"File exist\")' 2> /dev/null )" ]]; then
  logger "There is already a profiles refresh in progress, tailing:"
  docker logs --since 0.1s -f cloud-profiler 2>&1 | tee >(sed -n "/clouds/ q") | awk '1;/clouds/{exit}'
else
  logger "Issuing ad-hoc run."
  docker exec \
    cloud-profiler \
      python3 -c $'import os\nos.mknod("cut.tmp")'
  logger "Tailing logs for already running container:\n"
  docker logs --since 0.1s -f cloud-profiler 2>&1 | tee >(sed -n "/clouds/ q")| awk '/Start of loop/,/clouds/'
  logger "Tailing logs DONE.\n"
fi

docker ps -f name=cloud-profiler ; exit_state "Finding the service profile in docker ps"
exit 0
