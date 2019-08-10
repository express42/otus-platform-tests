
printf "Howdy! I will run [otus-platform-tests] locally for you.\n"

dirtocheck=""
platformdir=""
hwdir=""

if [[ ! -d $1 || "$2" == "" ]]; then
    printf "You'll supposed to point me in, I'll need to know where to start.\n"

    read -p "Your local platform folder (something like $HOME/src/{gitname}_platform):" platformdir

    if [ ! -d $platformdir ]; then
        printf "Does not look like a valid folder. You can do better!"
        exit 1
    fi

    read -p "Homework dir you want me to check (kubernetes-intro or others):" hwdir

    if [ "$hwdir" == "" ]; then
        printf "No in - no out! Point me somewhere to do the job."
        exit 1
    fi

    dirtocheck="$platformdir/$hwdir"
else
    platformdir="$1"
    hwdir="$2"
    dirtocheck="$platformdir/$hwdir"
fi

printf "\nYou pointed me here [$platformdir] to check [$hwdir]. I will obey! \n"
printf "\n"
cd $platformdir
export TRAVIS_BRANCH=$(echo $hwdir | tr -d '\r')

curl https://raw.githubusercontent.com/express42/otus-platform-tests/2019-06/run.sh | bash
