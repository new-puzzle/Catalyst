import { useState, useRef, useCallback } from 'react';
import { api } from '../services/api';

interface UseGoogleSpeechOptions {
  onResult: (transcript: string) => void;
  onError: (error: string) => void;
}

export function useGoogleSpeech({ onResult, onError }: UseGoogleSpeechOptions) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Browser speech recognition as fallback
  const useBrowserFallback = useCallback((audioBlob: Blob) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onError('Speech recognition not available');
      setIsProcessing(false);
      return;
    }

    // For browser fallback, we need to re-record since we can't use the blob
    // This is a limitation - browser API needs live audio
    onError('Google STT failed. Please try again with browser speech recognition.');
    setIsProcessing(false);
  }, [onError]);

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 48000,
        }
      });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm'
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });

        try {
          // Try Google Cloud STT first
          const result = await api.speechToText(audioBlob);
          if (result.transcript) {
            onResult(result.transcript);
          } else {
            onError('No speech detected');
          }
        } catch (err) {
          console.error('Google STT failed:', err);
          // Fall back to browser API indication
          useBrowserFallback(audioBlob);
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err) {
      onError('Microphone access denied');
    }
  }, [onResult, onError, useBrowserFallback]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsListening(false);
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  return {
    isListening,
    isProcessing,
    startListening,
    stopListening,
    toggleListening,
  };
}

// Type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
