const { v1: uuidv1 } = require('uuid');
const axios = require('axios');
const fs = require('fs');

module.exports = class Telemetry {
    constructor(session_id, did) {
        // fs.appendFileSync('telemetry-log.log', '', 'utf-8');
        
        this.events = [];
        this.session_id = session_id;
        const env = process.env.ENV;
        this.template = {
            "actor": {
                "id": "ivrs-service",
                "type": "System"
            },
            "context": {
                "channel": "ejp.ivrs",
                "did": did,
                "env": env,
                "pdata": {
                    "id": `${env}.ejp.ivrs`,
                    "pid": "ivrs-service",
                    "ver": "1.0"
                },
                "sid": this.session_id
            },
            "ver": "3.0"
        };
    }

    generate_mid(eid) {
        return `${eid}:${uuidv1()}`;
    }

    generate_event(eid, edata) {
        const event = { ...this.template };
        event["eid"] = eid;
        event["edata"] = edata;
        event["ets"] = parseInt(Date.now());
        event["mid"] = this.generate_mid(eid);

        this.events.push(event);
    }

    start(args) {
        let edata = {
            "type": "TOUCH",
            "subtype": "dtmf",
            "extra": {
                "keypad_input": args['input'],
                "audio_language": args['language'],
                "audio_type": args['audio_type'] || '',
                "audio_name": args['audio_name'] || '',
            }
        }
        this.generate_event("START", edata);
    }

    end() {
        const edata = {
            "mode": "end",
            "type": "session"
        };

        this.generate_event("END", edata);
    }

    push() {
        const data = JSON.stringify({ "events": this.events });
        let telemetry_synced = false;

        if (!!process.env.TELEMETRY_API_URL) {
            axios.post(process.env.TELEMETRY_API_URL, { "events": this.events }, {"headers":{"Content-Type":"application/json"}})
                .then(function (response) {
                    telemetry_synced = true;
                    console.log("telemetry sync success")
                })
                .catch(function (error) {
                    console.log("telemetry sync failed")
                });
        }

        // if (!telemetry_synced) {
        //     fs.appendFileSync('telemetry-log.log', `Telemetry events :: ${this.session_id} :: ${data}\n`, 'utf-8');
        // }

        this.events = [];
    }
}