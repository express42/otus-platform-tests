#!/bin/bash
GROUP=2019-12
BRANCH=${TRAVIS_PULL_REQUEST_BRANCH:-$TRAVIS_BRANCH}
HOMEWORK_RUN=./otus-platform-tests/homeworks/$BRANCH/run.sh
REPO=https://github.com/express42/otus-platform-tests.git
DOCKER_IMAGE=express42/otus-homeworks

echo GROUP:$GROUP

if [ "$BRANCH" == "" ]; then
	echo "We don't have tests for master branch"
	exit 0
fi

echo HOMEWORK:$BRANCH

echo "Clone repository with tests"
git clone -b $GROUP --single-branch $REPO

if [ -f $HOMEWORK_RUN ]; then
	echo "Run tests"
	/bin/bash $HOMEWORK_RUN
else
	echo "We don't have tests for this homework. Please check branch naming"
	exit 1
fi
