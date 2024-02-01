const express = require('express')
const axios = require('axios')
const app = express()
const port = 3000

function getDayOfYear(date) {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date - start;
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
}

async function getAudio(audioKey) {
  const urlData = process.env.IVRS_CONFIG_URL;
  // const urlData = "https://objectstorage.ap-hyderabad-1.oraclecloud.com/n/ax2cel5zyviy/b/sbdjp-ivrs/o/audio/ivrs_config.json"

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


app.get('/media', async (req, res) => {
  const language = req.query.language
  const category = req.query.category
  audioKey = `${category}:${language}`
  audioUrl = await getAudio(audioKey)

  if(!audioUrl) {
    audioKey = `${audioKey}:empty`
    audioUrl = await getAudio(audioKey)
  }

  if(!audioUrl) {
    audioKey = `invalid_option:${language}`
    audioUrl = await getAudio(audioKey)
  }

  res.send({url: audioUrl});
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})