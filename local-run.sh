#!/bin/bash
echo "Howdy! I will run [otus-platform-tests] locally for you."
echo
platformdir=""
hwdir=""

if [[ ! -d $1 || "$2" == "" ]]; then
    echo "You'll supposed to point me in, I'll need to know where to start."

    read -p "Your local platform folder (something like $HOME/src/{gitname}_platform):" platformdir

    if [ ! -d "$platformdir" ]; then
        echo "Does not look like a valid folder. You can do better!"
        exit 1
    fi

    read -p "Homework dir you want me to check (kubernetes-intro or others):" hwdir

    if [ "$hwdir" == "" ]; then
        echo "No in - no out! Point me somewhere to do the job."
        exit 1
    fi
else
    platformdir="$1"
    hwdir="$2"
fi

printf "\nYou pointed me here [%s] to check [%s]. I will obey! \n" "$platformdir" "$hwdir"
echo

pathtorunsh="$PWD/run.sh"

cd "$platformdir" || exit 1

TRAVIS_BRANCH=$(echo "$hwdir" | tr -d '\r')
export TRAVIS_BRANCH

bash "$pathtorunsh"
