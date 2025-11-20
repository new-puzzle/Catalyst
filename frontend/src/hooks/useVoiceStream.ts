import { useState, useRef, useCallback, useEffect } from 'react';

interface VoiceStreamOptions {
  onTextResponse: (text: string) => void;
  onStatusChange: (status: string) => void;
  onError: (error: string) => void;
  userId?: number;
  conversationId?: number;
}

export function useVoiceStream({ onTextResponse, onStatusChange, onError, userId, conversationId }: VoiceStreamOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);

  // Connect to voice stream
  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/voice/stream`);

    ws.onopen = () => {
      // Send init message with user and conversation IDs
      ws.send(JSON.stringify({
        type: 'init',
        user_id: userId,
        conversation_id: conversationId
      }));
      setIsConnected(true);
      onStatusChange('Connected');
    };

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'text':
          onTextResponse(message.data);
          break;

        case 'audio':
          // Queue audio for playback
          const audioData = base64ToArrayBuffer(message.data);
          audioQueueRef.current.push(audioData);
          if (!isPlayingRef.current) {
            playNextAudio();
          }
          break;

        case 'status':
          onStatusChange(message.data);
          break;

        case 'turn_complete':
          setIsSpeaking(false);
          break;

        case 'interrupted':
          // Clear audio queue on interruption
          audioQueueRef.current = [];
          setIsSpeaking(false);
          break;

        case 'error':
          onError(message.data);
          break;
      }
    };

    ws.onerror = () => {
      onError('Connection error');
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsStreaming(false);
      onStatusChange('Disconnected');
    };

    wsRef.current = ws;
  }, [onTextResponse, onStatusChange, onError, userId, conversationId]);

  // Disconnect
  const disconnect = useCallback(() => {
    stopStreaming();
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  // Start streaming audio
  const startStreaming = useCallback(async () => {
    if (!isConnected) {
      connect();
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      mediaStreamRef.current = stream;

      // Create audio context for processing
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          // Convert float32 to int16 PCM
          const pcmData = float32ToInt16(inputData);
          const base64 = arrayBufferToBase64(pcmData.buffer);

          wsRef.current.send(JSON.stringify({
            type: 'audio',
            data: base64
          }));
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsStreaming(true);
      onStatusChange('Listening...');
    } catch (err) {
      onError('Microphone access denied');
    }
  }, [isConnected, connect, onStatusChange, onError]);

  // Stop streaming
  const stopStreaming = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Signal end of turn
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_turn' }));
    }

    setIsStreaming(false);
    onStatusChange('Processing...');
  }, [onStatusChange]);

  // Interrupt AI response (barge-in)
  const interrupt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
      audioQueueRef.current = [];
      setIsSpeaking(false);
    }
  }, []);

  // Send text message
  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', data: text }));
    }
  }, []);

  // Play audio from queue
  const playNextAudio = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    setIsSpeaking(true);

    const audioData = audioQueueRef.current.shift()!;

    try {
      const audioContext = new AudioContext({ sampleRate: 24000 }); // Gemini outputs at 24kHz
      const audioBuffer = await audioContext.decodeAudioData(audioData);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);

      source.onended = () => {
        audioContext.close();
        playNextAudio();
      };

      source.start();
    } catch (err) {
      console.error('Audio playback error:', err);
      playNextAudio();
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isStreaming,
    isSpeaking,
    connect,
    disconnect,
    startStreaming,
    stopStreaming,
    interrupt,
    sendText
  };
}

// Utility functions
function float32ToInt16(float32Array: Float32Array): Int16Array {
  const int16Array = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return int16Array;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}
