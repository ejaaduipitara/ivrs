const express = require('express')
const crypto = require('crypto');
const bodyParser = require('body-parser')

const axios = require('axios')
const Telemetry = require('./telemetry')
const app = express()

const port = 8000

app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json())

const CATEGORIES = ["story", "song", "question"]

function getDayOfYear(date) {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date - start;
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
}

async function getAudio(audioKey) {
  const urlData = process.env.IVRS_CONFIG_URL;

  try {
    getDayOfYear(new Date())
    const response = await axios.get(urlData);
    config = response.data

    if (!(audioKey in config)) {
        return null;
    }

    const numberOfAudios = config[audioKey].length;
    const dayOfYear = getDayOfYear(new Date())
    const modDayNo = dayOfYear % numberOfAudios;

    const audioIndex = modDayNo === 0 ? numberOfAudios : modDayNo;

    return config[audioKey][audioIndex - 1];
  } catch (error) {
    console.error('Error:', error.message);
    return null;
  }
}

app.get('/health', async (req, res) => {
  res.send({"status":"success","healthy":true  });
})


app.post('/media', async (req, res) => {
  let sessionId = req.body.call_id
  var did = crypto.createHash('md5').update(req.body.caller_id_number).digest('hex');
  let telemetry = new Telemetry(sessionId, did)

  console.log(`Session started: ${sessionId}`)

  let userInputFlow = req.body.call_flow
  const dtmfObj = userInputFlow.pop()
  const languageObj = userInputFlow.pop()
  
  category = CATEGORIES[parseInt(dtmfObj.input) - 1]
  language = languageObj.name.trim().toLowerCase()
  audioKey = `${category}:${language}`
  audioUrl = await getAudio(audioKey)
  console.log(`${sessionId} :: audioKey :: ${audioKey}`)

  if(!audioUrl) {
    audioKey = `${audioKey}:empty`
    audioUrl = await getAudio(audioKey)
  }

  if(!audioUrl) {
    audioKey = `invalid_option:${language}`
    audioUrl = await getAudio(audioKey)
  }

  resultObj = [{
    "recording": {
      "type": "url",
      "data": audioUrl
    }
  }]

  startEdata = {
    "input": parseInt(dtmfObj.input),
    "language": language,
    "audio_type": category,
    "audio_name": audioUrl
  }
  telemetry.start(startEdata)

  telemetry.end()
  telemetry.push()
  console.log(`${sessionId} :: response :: ${JSON.stringify(resultObj)}`)
  res.send(resultObj);
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})