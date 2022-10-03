#!/bin/bash

IMAGE_TAG="zigbee_2_mqtt_client:zigbee_2_mqtt_client_latest"
IMAGE_ID=$(docker images -q $IMAGE_TAG)

#echo -e "${IMAGE_ID}"
docker run -d --network=host --restart=on-failure:5 ${IMAGE_ID}
