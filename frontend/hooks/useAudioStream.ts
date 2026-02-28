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
      // Inside hooks/useAudioStream.ts
      socket.current.onmessage = (event) => {
        try {
          // 1. First, try to read it as JSON (For Block 3: Action Items)
          const data = JSON.parse(event.data);
          
          if (data.type === 'action_item') {
            setActionItems((prev) => [...prev, data.item]);
          }
        } catch (error) {
          // 2. If it is NOT JSON, it must be the raw transcript text from Person A!
          // Voxtral sends chunks like "I ", "will ", "do ", "that."
          setTranscript((prev) => prev + event.data);
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