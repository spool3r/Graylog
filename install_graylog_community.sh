#!/bin/bash

clear

# Installing Mongo
printf "\nInstalling Mongo...\n\n"
docker run --name mongo -d mongo

# Installing OpenSearch
printf "\nInstalling OpenSearch...\n"
printf "\nEnter the OpenSearch Admin Password: "
OPENSEARCH_PASSWORD="$(echo -n "" && head -1 < /dev/stdin | tr -d '\n' | cut -d " " -f1)"
printf "\n"
docker run -it -p 9200:9200 -p 9600:9600 -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=$OPENSEARCH_PASSWORD -e "discovery.type=single-node" -e DISABLE_SECURITY_PLUGIN=true -d --name opensearch-node opensearchproject/opensearch:2.12.0
printf "\nWaiting for OpenSearch to load...\n"
sleep 60s
curl http://localhost:9200 -ku 'admin:'$OPENSEARCH_PASSWORD
read -n1 -p "Did it connect? [y,n]" OpenSearchResponse 
case $OpenSearchResponse in  
  y|Y) printf "\nGreat, continuing on\n" ;; 
  n|N) printf "\n\nTime to check the logs\n" && exit 1 ;; 
esac

# Installing Graylog
printf "\nInstalling Graylog...\n"
printf "\nEnter the Graylog Admin Password: "
GRAYLOG_ROOT_PASSWORD_SHA2="$(echo -n "" && head -1 < /dev/stdin | tr -d '\n' | sha256sum | cut -d " " -f1)"
GRAYLOG_PASSWORD_SECRET="$(pwgen -N 1 -s 96)"
printf "\nGetting local ip address...\n"
LocalIP="$(ip -o route get to 8.8.8.8 | sed -n 's/.*src \([0-9.]\+\).*/\1/p')"
printf "\nInstalling Graylog Docker Container...\n"
docker run --link mongo --link opensearch-node -p 9000:9000 -p 12201:12201 -p 1514:1514 -p 5555:5555 -e GRAYLOG_ROOT_PASSWORD_SHA2=$GRAYLOG_ROOT_PASSWORD_SHA2 -e GRAYLOG_PASSWORD_SECRET=$GRAYLOG_PASSWORD_SECRET -e GRAYLOG_HTTP_EXTERNAL_URI="http://$LocalIP:9000/" -e GRAYLOG_HTTP_PUBLISH_URI="http://$LocalIP:9000/" -e GRAYLOG_ELASTICSEARCH_HOSTS="http://admin:$OPENSEARCH_PASSWORD@$LocalIP:9200" --name greylog -d graylog/graylog:6.0.4

# Wrapping Up
printf "\nInstallation complete. Log in at http://$LocalIP:9000 in a few minutets.\n"
