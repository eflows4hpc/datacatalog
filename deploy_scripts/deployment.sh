#!/bin/bash

## USAGE:
#
# deployment.sh <git_directory> [CHECKOUT_TAG] [API_URL] [SERVER_DOMAIN]

OLD_DIR=`pwd`

if [ -z "$1" ]; then 1=`pwd`; fi
if [ -z "$2" ]; then CHECKOUT_TAG=master; else CHECKOUT_TAG=$2; fi
if [ -z "$3" ]; then API_URL=https://datacatalog.fz-juelich.de/; else API_URL=$3; fi
if [ -z "$4" ]; then SERVER_DOMAIN=datacatalog.fz-juelich.de; else SERVER_DOMAIN=$4; fi

cd $1

git pull --all
git checkout $CHECKOUT_TAG

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