import { useState, useRef, useCallback } from 'react';

export const useAudioStream = (websocketUrl: string) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState<string>('');
  const [actionItems, setActionItems] = useState<any[]>([]);
  
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const socket = useRef<WebSocket | null>(null);

  const startRecording = useCallback(async () => {
    try {
      // 1. Open WebSocket connection to your partner's FastAPI server
      socket.current = new WebSocket(websocketUrl);
      
      // 2. Listen for processed data coming BACK from the AI
      socket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'transcript') {
          setTranscript((prev) => prev + ' ' + data.text);
        } else if (data.type === 'action_item') {
          setActionItems((prev) => [...prev, data.item]);
        }
      };

      // 3. Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });

      // 4. Send audio chunks to the server every 1 second
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socket.current?.readyState === WebSocket.OPEN) {
          socket.current.send(event.data);
        }
      };

      mediaRecorder.current.start(1000); // 1000ms chunks
      setIsRecording(true);
      
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  }, [websocketUrl]);

  const stopRecording = useCallback(() => {
    mediaRecorder.current?.stop();
    socket.current?.close();
    setIsRecording(false);
  }, []);

  return { isRecording, startRecording, stopRecording, transcript, actionItems };
};