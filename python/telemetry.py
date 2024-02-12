from copy import deepcopy
from urllib import request


import logging
import json
import uuid
import os
import time

class Telemetry:
    def __init__(self, session_id, did):
        logging.basicConfig(filename='telemetry-log.log', encoding='utf-8', level=logging.INFO)

        self.events = []
        self.session_id = session_id
        env = os.environ['ENV']
        self.template = {
          "actor": {
            "id": "ivrs-service",
            "type": "System"
          },
          "context": {
            "channel": "ejp.ivrs",
            "did": did,
            "env": env,
            "pdata": {
              "id": f"{env}.ejp.ivrs",
              "pid": "ivrs-service",
              "ver": "1.0"
            },
            "sid": self.session_id
          },
          "ver": "3.0",
        }

    def generate_mid(self, eid):
        return f"{eid}:{str(uuid.uuid1())}"
      
    def is_not_blank(self, s):
        return bool(s and not s.isspace())

    def generate_event(self, eid, edata):
        event = deepcopy(self.template)
        event["eid"] = eid
        event["edata"] = edata
        event["ets"] = int(time.time() * 1000)
        event["mid"] = self.generate_mid(eid)
        
        self.events.append(event)

    def start(self, edata):
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
        data = json.dumps({ "events": self.events })
        telemetry_not_synced = False

        if ('TELEMETRY_API_URL' in os.environ) and self.is_not_blank(os.environ['TELEMETRY_API_URL']):
            req = request.Request(os.environ['TELEMETRY_API_URL'], method="POST")
            req.add_header('Content-Type', 'application/json')
            data = data.encode()
            r = request.urlopen(req, data=data)
            content = r.read()
            print(content)
            telemetry_not_synced = True

        if telemetry_not_synced == False:
            logging.info(f"Telemetry events :: {self.session_id} :: {data}")

        self.events = []
