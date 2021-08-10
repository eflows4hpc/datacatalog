#!/bin/bash

OLD_DIR=`pwd`

if [ -z "$1" ]; then 1=`pwd`; fi

cd $1

git pull --all
if [ -z "$CHECKOUT_TAG" ]; then export CHECKOUT_TAG=master; fi
git checkout $CHECKOUT_TAG
if [ -z "$API_URL" ]; then export API_URL=https://datacatalog.fz-juelich.de/; fi
if [ -z "$SERVER_DOMAIN" ]; then export SERVER_DOMAIN=datacatalog.fz-juelich.de; fi

pip install -r requirements.txt

python3 frontend/createStatic.py -u $API_URL

sed -i "s_datacatalog.fz-juelich.de_${SERVER_DOMAIN}_g" docker-compose.yml

# it is at this point assumed that ip and volume are correctly assigned, and that dns is working properly

docker-compose pull #  pull changed images (e.g. new latest, or specific tag)
TIME=`date +%Y-%m-%d-%H-%M`
mv /app/mnt/docker.log "/app/mnt/docker.log.${TIME}"

docker-compose up -d # should only restart changed images, which will also update nginx and reverse-proxy image if needed

nohup docker-compose logs -f >/app/mnt/docker.log & # or similar to capture docker log TODO

cd $OLD_DIR