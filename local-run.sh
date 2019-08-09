
echo "Howdy! I will run [otus-platform-tests] locally for you.\n"

dirtocheck=""
platformdir=""
hwdir=""

if [[ ! -d $1 || "$2" == "" ]]; then
    echo "You'll supposed to point me in, I'll need to know where to start.\n"

    read -p "Your local platform folder (something like $HOME/src/{gitname}_platform):" platformdir

    if [ ! -d $platformdir ]; then
        echo "Does not look like a valid folder. You can do better!"
        exit 1
    fi

    read -p "Homework dir you want me to check (kubernetes-intro or others):" hwdir

    if [ "$hwdir" == "" ]; then
        echo "No in - no out! Point me somewhere to do the job."
        exit 1
    fi

    dirtocheck="$platformdir/$hwdir"
else
    hwdir="$2"
    dirtocheck="$1/$hwdir"
fi

echo "\nYou pointed me here [$dirtocheck]. I will obey! \n"

cd $dirtocheck
export TRAVIS_BRANCH=$(echo $hwdir | tr -d '\r')

curl https://raw.githubusercontent.com/express42/otus-platform-tests/2019-06/run.sh | bash
