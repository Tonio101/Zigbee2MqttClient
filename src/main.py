import argparse
import json
import logging
import os
import queue
import sys

from time import sleep
from threading import Lock
from logger import Logger
from influxdb_client import InfluxDbClient
from mqtt_client import MQTTClient
from devices import DeviceFactory
from device_events import DeviceEvents

log = Logger.getInstance().getLogger()

Q_SIZE = 128


def parse_config_file(fname: str) -> dict:
    with open(os.path.abspath(fname), 'r') as fp:
        data = json.load(fp)
        return data


def configure_mqtt_client(config: dict) -> MQTTClient:
    client = \
        MQTTClient(username=config['user'],
                   password=config['pasw'],
                   mqtt_host=config['host'],
                   mqtt_port=config['port'])
    client.set_event_topic(topic=config['mqttTopic'])
    return client


def configure_sensors(mqtt_client: MQTTClient, config: dict) -> dict:
    influxdb_config = config['influxdb']
    influx_db_enabled = config['features']['influxDB']

    device_hash = dict()

    for device_info in config['sensors']:
        device_topic = device_info['mqttTopic']

        device = DeviceFactory(device_info['type'], device_info)
        device.set_mqtt_client(mqtt_client=mqtt_client)

        if influx_db_enabled:
            client = \
                InfluxDbClient(url=influxdb_config['url'],
                               auth=(influxdb_config['auth']['user'],
                                     influxdb_config['auth']['pasw']),
                               db_name=influxdb_config['dbName'],
                               measurement=device_info['infludbMeasurement'],
                               tag_set=device_info['influxdbTagSet'])
            device.set_influxdb_client(influxdb_client=client)

        device_hash[device_topic] = device

    return device_hash


def main(argv):
    usage = ("{FILE} --config <config_file> --debug").format(FILE=__file__)
    description = 'Zigbee MQTT Sensor Data'
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument("-c", "--config", help="Configuration file",
                        required=True)
    parser.add_argument("--debug", help="Enable verbose logging",
                        action='store_true', required=False)
    parser.set_defaults(debug=False)

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    config = parse_config_file(args.config)
    log.debug(config)

    featuresConfig = config['features']
    mqtt_enabled = featuresConfig['localMQTT']
    configured_queue_size = featuresConfig['inputQueueSize']

    mqtt_broker_config = config['mqttBroker']

    input_queue = None
    mqtt_client = None

    lock = Lock()

    if configured_queue_size:
        input_queue = queue.Queue(maxsize=configured_queue_size)
    else:
        input_queue = Q_SIZE

    if mqtt_enabled:
        mqtt_client = configure_mqtt_client(config=mqtt_broker_config)
        if mqtt_client and input_queue:
            mqtt_client.set_input_queue(lock=lock, input_queue=input_queue)
        mqtt_client.connect_to_broker()

    device_hash = configure_sensors(mqtt_client=mqtt_client, config=config)
    log.debug("Device Hash Map: {}".format(device_hash))
    event_thread = DeviceEvents(lock=lock,
                                event_queue=input_queue,
                                device_hash=device_hash)
    event_thread.start()
    event_thread.join()


if __name__ == '__main__':
    main(sys.argv)
