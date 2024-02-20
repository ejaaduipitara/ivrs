const { WebSocket, WebSocketServer } = require('ws');
const http = require('http');
const uuidv4 = require('uuid').v4;
const fs = require('fs');

// Create an HTTP server and a WebSocket server
const server = http.createServer();
const wsServer = new WebSocketServer({ server: server, path: '/media' });
const port = 8000;

// Start the WebSocket server
server.listen(port, () => {
  console.log(`WebSocket server is running on port ${port}`);
});

// Maintain active connections and users
const clients = {};
const users = {};
let userActivity = [];
let audioStreamEvents = {};
// let globalStream = fs.createWriteStream('all-requests.log',{ flags: 'w'});

// Handle new client connections
wsServer.on('connection', function handleNewConnection(ws) {
  const userId = uuidv4();
  console.log('Received a new connection');

  clients[userId] = ws;
  console.log(`${userId} connected.`);

  ws.on('message', (message) => processReceivedMessage(message, userId, ws));
  ws.on('close', () => handleClientDisconnection(userId));
});


// Handle incoming messages from clients
function processReceivedMessage(message, userId, ws) {
    const dataFromClient = JSON.parse(message.toString());
    users[userId] = dataFromClient;
    const event = dataFromClient.event;
    if (event === 'connected') {
        console.log(`${userId} connected for audio streaming.`);
    } else if (event === 'start') {
        const sId = dataFromClient.start.stream_sid;
        console.log(`${userId} starting the streaming using ${sId}.`);
        audioStreamEvents[userId] = [];
    } else if (event === 'media') {
        audioStreamEvents[userId].push(message);
    } else if (event === 'stop') {
        console.log(`${userId} stop with sequence_number ${dataFromClient.sequence_number}.`);
    } else if (event === 'mark') {
        console.log(`${userId} mark with sequence_number ${dataFromClient.sequence_number}.`);
    } else if (event === 'dtmf') {
        const dtmfInput = dataFromClient.dtmf.digit;
        console.log(`${userId} dtmf with sequence_number ${dataFromClient.sequence_number} by pressing ${dtmfInput}.`);
        if (dtmfInput == "9") {
            const stream_sid = dataFromClient.stream_sid;
            const markSeq = parseInt(dataFromClient.sequence_number) + 1;
            replayAudio(userId);
        } else {
            console.log("dtmf message is " + dtmfInput + " so, not replaying the audio.");
        }
    } else {
        console.log("message with unknown event type: " + JSON.stringify(dataFromClient));
    }

}

function replayAudio(userId) {
    for(const index in audioStreamEvents[userId]) {
        const msg = audioStreamEvents[userId][index];
        ws.send(msg);
    }
    let markEvent = {"event":"mark","sequence_number":markSeq,"stream_sid":stream_sid,"mark":{"name":"reply complete"}};
    let markStr = JSON.stringify(markEvent);
    console.log("Mark event: " + markStr);
    ws.send(Buffer.from(markStr));
    audioStreamEvents[userId] = [];
}

// Handle disconnection of a client
function handleClientDisconnection(userId) {
    console.log(`${userId} disconnected.`);
    const json = {};
    const username = users[userId]?.username || userId;
    userActivity.push(`${username} left the editor`);
    json.data = { users, userActivity };
    delete clients[userId];
    delete users[userId];
    console.log("User activity: " + JSON.stringify(json));
}
