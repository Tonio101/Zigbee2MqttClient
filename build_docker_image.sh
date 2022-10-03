#!/bin/bash

IMAGE_TAG="zigbee_2_mqtt_client:zigbee_2_mqtt_client_latest"
DOCKER_FILE=$(/bin/pwd)/Dockerfile

#echo -e "${IMAGE_TAG}\n${DOCKER_FILE}\n"

docker build --tag ${IMAGE_TAG} .
