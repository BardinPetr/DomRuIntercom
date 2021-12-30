from datetime import datetime
from json import dumps
from random import randint
from threading import Timer
from uuid import getnode as get_mac

from paho.mqtt import client as mqtt_client


class HASSDeviceTrigger:
    def __init__(self, host, port, user, password, access_control_id):
        self._acid = access_control_id

        self._mqtt = mqtt_client.Client(f'domru-intercom_opener-{randint(0, 1000)}')
        self._mqtt.username_pw_set(user, password)
        self._mqtt.connect(host, port)

        self._timer = Timer(60, self._discovery)
        self._timer.start()

    def _discovery(self):
        node = f"domru_{self._acid}"
        self._mqtt.publish(f'homeassistant/device_automation/domru_opener/{node}/config',
                           dumps({
                               "automation_type": "trigger",
                               "type":            "user_enter",
                               "subtype":         "main",
                               # "payload":         "",
                               "topic":           f"homeassistant/{node}/user_enter",
                               "device":          {
                                   "identifiers":  [f"domruopener-{node}"],
                                   "name":         node,
                                   "sw_version":   "DomRu IntercomOpener v1.0.0",
                                   "model":        "default",
                                   "manufacturer": "BPA"
                               }
                           }
                           ))

    def opened(self, user):
        self._mqtt.publish(f'homeassistant/domru_{self._acid}/user_enter', dumps({
            "time":     int(datetime.now().timestamp()),
            "person":   user[0],
            "distance": user[1][0]
        }))
