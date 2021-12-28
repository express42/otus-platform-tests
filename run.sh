#!/bin/bash
GROUP=2021-12
BRANCH=${GITHUB_REF##*/}
HOMEWORK_RUN=./otus-platform-tests/homeworks/$BRANCH/run.sh
REPO=https://github.com/express42/otus-platform-tests.git
DOCKER_IMAGE=express42/otus-homeworks

echo GROUP:$GROUP
echo BRANCH:$BRANCH

if [ "$BRANCH" == "" ]; then
	echo "We dont have tests for master branch"
	exit 0
fi

if [ -f $HOMEWORK_RUN ]; then
	echo "Run tests"
	/bin/bash $HOMEWORK_RUN
else
	echo "We dont have tests for this homework. Please check branch naming"
	exit 1
fi
