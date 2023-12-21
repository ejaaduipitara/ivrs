from copy import deepcopy
from urllib import request

import json
import uuid
import os
import time

class Telemetry:
    def __init__(self, session_id):
        self.events = []
        self.session_id = session_id
        self.template = {
          "actor": {
            "id": self.session_id,
            "type": "System"
          },
          "context": {
            "channel": "IVRS-channel",
            "did": "IVRS-system",
            "env": "IVRS",
            "pdata": {
              "id": "producer1",
              "pid": "genieservice.android",
              "ver": "1.0"
            },
            "sid": self.session_id
          },
          "mid": "92a9a779-ea2c-4f4e-8d07-fc7c3e851993",
          "ver": "3.0",
        }

    def generate_mid(self, eid):
        return f"{eid}:{str(uuid.uuid1())}"

    def generate_event(self, eid, edata):
        event = deepcopy(self.template)
        event["eid"] = eid
        event["edata"] = edata
        event["ets"] = int(time.time() * 1000)
        event["mid"] = self.generate_mid(eid)
        
        self.events.append(event)

    def start(self):
        edata = {
          "mode": "start",
          "type": "session"
        }

        self.generate_event("START", edata)     
        
    def interact(self, **args):
        edata = {
          "type": "TOUCH",
          "subtype": "dtmf",
          "extra": {
            "keypad_input": args['input'],
            "audio_language": args['language'],
            "audio_type": args['audio_type'] if 'audio_type' in args else '', # empty string for invalid input
            "audio_name": args['audio_name'] if 'audio_name' in args else '', # empty string for invalid input
          }
        }
        
        self.generate_event("INTERACT", edata)
        
    def end(self):
        edata = {
          "mode": "end",
          "type": "session"
        }

        self.generate_event("END", edata)

    def push(self):
        print(self.events)
        req = request.Request(os.environ['TELEMETRY_API_URL'], method="POST")
        req.add_header('Content-Type', 'application/json')
        data = {
            "events": self.events
        }
        data = json.dumps(data)
        data = data.encode()
        r = request.urlopen(req, data=data)
        content = r.read()
        print(content)
        self.events = []
