import { useState, useRef, useCallback, useEffect } from 'react';

interface VoiceStreamOptions {
  onTextResponse: (text: string) => void;
  onAudioResponse?: (audioData: string) => void;
  onError: (error: string) => void;
}

export function useVoiceStream({ onTextResponse, onAudioResponse, onError }: VoiceStreamOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/voice/stream`);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Voice stream connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'text':
          onTextResponse(message.data);
          break;
        case 'audio':
          onAudioResponse?.(message.data);
          break;
        case 'status':
          console.log('Stream status:', message.data);
          break;
        case 'error':
          onError(message.data);
          break;
      }
    };

    ws.onerror = () => {
      onError('WebSocket connection error');
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('Voice stream disconnected');
    };

    wsRef.current = ws;
  }, [onTextResponse, onAudioResponse, onError]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', data: text }));
    }
  }, []);

  const startStreaming = useCallback(async () => {
    if (!isConnected) {
      connect();
      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          // Convert to base64 and send
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64 = (reader.result as string).split(',')[1];
            wsRef.current?.send(JSON.stringify({ type: 'audio', data: base64 }));
          };
          reader.readAsDataURL(event.data);
        }
      };

      mediaRecorder.start(1000); // Send chunks every second
      mediaRecorderRef.current = mediaRecorder;
      setIsStreaming(true);
    } catch (err) {
      onError('Microphone access denied');
    }
  }, [isConnected, connect, onError]);

  const stopStreaming = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      mediaRecorderRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
      stopStreaming();
    };
  }, [disconnect, stopStreaming]);

  return {
    isConnected,
    isStreaming,
    connect,
    disconnect,
    sendText,
    startStreaming,
    stopStreaming
  };
}
