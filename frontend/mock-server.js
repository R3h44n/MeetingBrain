const WebSocket = require('ws');

// Start a WebSocket server on port 8080
const wss = new WebSocket.Server({ port: 8080 });

console.log('Mock AI Backend running on ws://localhost:8080');

wss.on('connection', (ws) => {
  console.log('Frontend connected! Ready to receive audio.');

  let chunkCount = 0;

  ws.on('message', (message) => {
    // 'message' will be the raw binary audio chunk from your microphone
    chunkCount++;
    console.log(`Received audio chunk #${chunkCount} (${message.length} bytes)`);

    // 1. Simulate the live transcript (Voxtral Realtime)
    // We send a fake transcript update every time we get an audio chunk
    const fakeTranscript = JSON.stringify({
      type: 'transcript',
      text: `[Audio chunk ${chunkCount} processed] `
    });
    ws.send(fakeTranscript);

    // 2. Simulate Mistral Large 3 extracting an action item
    // We will randomly send an action item every ~5 chunks to test your UI
    if (chunkCount % 5 === 0) {
      console.log('Simulating AI action item extraction...');
      const fakeActionItem = JSON.stringify({
        type: 'action_item',
        item: {
          title: `Setup Database Schema v${chunkCount/5}`,
          assignee: 'Person A',
          deadline: 'End of Day'
        }
      });
      ws.send(fakeActionItem);
    }
  });

  ws.on('close', () => {
    console.log('Frontend disconnected. Meeting ended.');
  });
});