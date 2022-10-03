import json

from time import sleep
from threading import Thread
from logger import Logger
log = Logger.getInstance().getLogger()


class DeviceEvents(Thread):

    def __init__(self,
                 lock,
                 event_queue,
                 device_hash):
        Thread.__init__(self)
        self.setDaemon(True)
        self.lock = lock
        self.event_queue = event_queue
        self.device_hash = device_hash

    def process_entry(self, msg) -> int:
        topic = msg.topic

        if topic not in self.device_hash:
            # log.debug(("{} is not "
            #           "in device hash").format(topic))
            return 0

        payload = json.loads(msg.payload.decode("utf-8"))
        self.device_hash[topic].refresh_device_data(payload)
        device = self.device_hash[topic]
        log.debug("\n{0}\n".format(device))

        rc = 0
        try:
            rc = device.process()
        except Exception as e:
            log.error(e)
            rc = -1

        return rc

    def process_events(self):
        if not self.event_queue.empty():
            self.lock.acquire()
            msg = self.event_queue.get()
            self.lock.release()
            rc = self.process_entry(msg)
            if rc != 0:
                log.error("Failed to process entry {0}".format(
                    rc
                ))

    def run(self):
        while True:
            if self.event_queue:
                self.process_events()
            sleep(1)
