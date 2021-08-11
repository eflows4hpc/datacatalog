#!/bin/bash

## USAGE:
#
# deployment.sh <git_directory> [CHECKOUT_TAG] [API_URL] [SERVER_DOMAIN]

OLD_DIR=`pwd`

echo "DEBUG_1 $0 $1 $2 $3 $4"

if [ -z ${1+x} ]; then NEW_DIR=`pwd`; fi
if [ -z ${2+x} ]; then CHECKOUT_TAG=master; else CHECKOUT_TAG=$2; fi
if [ -z ${3+x} ]; then API_URL=https://datacatalog.fz-juelich.de/; else API_URL=$3; fi
if [ -z ${4+x} ]; then SERVER_DOMAIN=datacatalog.fz-juelich.de; else SERVER_DOMAIN=$4; fi

echo "DEBUG_2 $0 $1 $2 $3 $4"

cd $NEW_DIR

git pull --all
git checkout -f $CHECKOUT_TAG

pip install -r requirements.txt

python3 frontend/createStatic.py -u $API_URL

sed -i "s_datacatalog.fz-juelich.de_${SERVER_DOMAIN}_g" docker-compose.yml

# it is at this point assumed that ip and volume are correctly assigned, and that dns is working properly

docker-compose pull #  pull changed images (e.g. new latest, or specific tag)
TIME=`date +%Y-%m-%d-%H-%M`
mv /app/mnt/docker.log "/app/mnt/docker.log.${TIME}"

docker-compose up -d # should only restart changed images, which will also update nginx and reverse-proxy image if needed

# nohup docker-compose logs -f >/app/mnt/docker.log & # or similar to capture docker log TODO (seems to cause gitlab CI to hang)

cd $OLD_DIR