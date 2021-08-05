#!/bin/bash

OLD_DIR=`pwd`

cd $1

git pull --all
if [ -z "$CHECKOUT_TAG" ]; then export CHECKOUT_TAG=master; fi
git checkout $CHECKOUT_TAG
if [ -z "$API_URL" ]; then export API_URL=https://datacatalog.fz-juelich.de/; fi

pip install -r requirements.txt

python3 frontend/createStatic.py -u $API_URL

# it is at this point assumed that ip and volume are correctly assigned, and that dns is working properly

nohup docker-compose up >/app/mnt/docker.log & # or similar to capture docker log TODO

cd $OLD_DIR