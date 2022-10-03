from datetime import datetime

from enum import Enum
from influxdb_client import InfluxDbClient
from mqtt_client import MQTTClient
from logger import Logger
log = Logger.getInstance().getLogger()


class DeviceType(Enum):
    DOOR = 1
    TEMPERATURE = 2
    LEAK = 3
    VIBRATION = 4


class TempType(Enum):
    CELSIUS = 1
    FAHRENHEIT = 2


class DoorEvent(Enum):
    UNKNOWN = -1
    OPEN = 1
    CLOSE = 2


class LeakEvent(Enum):
    UNKNOWN = -1
    DRY = 1
    FULL = 2


class VibrateEvent(Enum):
    UNKNOWN = -1
    NO_VIBRATE = 1
    VIBRATE = 2


DEVICE_TYPE = {
    "DoorSensor": DeviceType.DOOR,
    "THSensor": DeviceType.TEMPERATURE,
    "LeakSensor": DeviceType.LEAK,
    "VibrationSensor": DeviceType.VIBRATION
}

EVENT_STATE = {
    "normal": -1,
    "error": -1,
    "alert": -1,
    "open": DoorEvent.OPEN,
    "closed": DoorEvent.CLOSE,
    "dry": LeakEvent.DRY,
    "full": LeakEvent.FULL,
    "vibrate": VibrateEvent.VIBRATE
}

DEVICE_TYPE_TO_STR = {
    DeviceType.DOOR: "Door Sensor",
    DeviceType.TEMPERATURE: "Temperature Sensor",
    DeviceType.LEAK: "Leak Sensor",
    DeviceType.VIBRATION: "Vibration Sensor"
}


class Device(object):

    def __init__(self, device_info):
        self.type = DEVICE_TYPE[device_info['type']]
        self.device_id = device_info['deviceId']
        self.friendly_name = device_info['friendlyName']
        self.model = device_info['model']
        self.mqttTopic = device_info['mqttTopic']

        self.mqtt_client = None
        self.influxdb_client = None

        # Device data from each MQTT event received
        self.event_payload = {}

    def get_type(self):
        return self.type

    def get_device_id(self):
        return self.device_id

    def get_friendly_name(self):
        return self.friendly_name

    def refresh_device_data(self, data):
        self.event_payload = data

    def get_device_event_time(self):
        return datetime.fromtimestamp(
                self.event_payload['time'] / 1000)\
                .strftime("%Y-%m-%d %H:%M:%S")

    def get_current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_device_data(self):
        return self.event_payload

    def set_influxdb_client(self, influxdb_client: InfluxDbClient):
        self.influxdb_client = influxdb_client

    def set_mqtt_client(self, mqtt_client: MQTTClient):
        self.mqtt_client = mqtt_client

    def influxdb_write_device_data(self, data):
        if self.influxdb_client:
            return self.influxdb_client.write_data(data)
        else:
            log.info(data)
            return 0

    def process(self):
        """
        Every object that inherits Device object
        should implement the process function.

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    def __str__(self):
        to_str = ("Friendly Name: {}\nType: {}\n"
                  "Current Time: {}\n").format(
                      self.friendly_name,
                      DEVICE_TYPE_TO_STR[self.type],
                      self.get_current_time()
        )

        return to_str


class TemperatureDevice(Device):

    def __init__(self, device_info):
        super().__init__(device_info)
        self.temp = 0.0

    def get_temperature(self, type=TempType.FAHRENHEIT):
        try:
            self.temp = float(self.get_device_data()['temperature'])

            if type == TempType.FAHRENHEIT:
                return round(((self.temp * 1.8) + 32), 2)

            return round(self.temp, 2)
        except Exception as e:
            return None

    def get_humidity(self):
        try:
            return round(float(self.get_device_data()['humidity']), 2)
        except Exception as e:
            return None

    def influxdb_write_data(self):
        temperature_data = self.get_temperature()
        humidity_data = self.get_humidity()

        if temperature_data and humidity_data: 
            data = ("temperature={0},humidity={1}").format(
                str(temperature_data),
                str(humidity_data)
            )
            return self.influxdb_write_device_data(data)

        return 0

    def __str__(self):
        to_str = ("Temperature (F): {0}\nHumidity: {1}\n").format(
            self.get_temperature(),
            self.get_humidity()
        )
        return super().__str__() + to_str

    def process(self):
        if self.influxdb_client:
            return self.influxdb_write_data()

        return 0


def DeviceFactory(type: str, device_info: dict) -> Device:
    """
    Factory Method

    Args:
        type (str): Device type.
        device_info (dict): Device info.

    Returns:
        Device: Device Object.
    """
    device_localizers = {
        # "DoorSensor": DoorDevice,
        "THSensor": TemperatureDevice,
        # "LeakSensor": LeakDevice,
        # "VibrationSensor": VibrationDevice,
    }

    return device_localizers[type](device_info=device_info)
