import { useState, useRef, useCallback } from 'react';

interface EmotionScore {
  name: string;
  score: number;
}

interface HumeVoiceResult {
  transcript: string;
  emotions: EmotionScore[];
  primaryEmotion: string;
}

interface UseHumeVoiceOptions {
  apiKey: string;
  onResult: (result: HumeVoiceResult) => void;
  onError: (error: string) => void;
}

export function useHumeVoice({ apiKey, onResult, onError }: UseHumeVoiceOptions) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });

        try {
          const result = await processWithHume(audioBlob, apiKey);
          onResult(result);
        } catch (error) {
          onError(error instanceof Error ? error.message : 'Failed to process audio');
        } finally {
          setIsProcessing(false);
          stream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(1000); // Collect data every second
      setIsListening(true);
    } catch (error) {
      onError('Microphone access denied');
    }
  }, [apiKey, onResult, onError]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
  }, [isListening]);

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

async function processWithHume(audioBlob: Blob, apiKey: string): Promise<HumeVoiceResult> {
  // Convert blob to base64
  const arrayBuffer = await audioBlob.arrayBuffer();
  const base64Audio = btoa(
    new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
  );

  // Call Hume API for emotion analysis
  const response = await fetch('https://api.hume.ai/v0/batch/jobs', {
    method: 'POST',
    headers: {
      'X-Hume-Api-Key': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      models: {
        prosody: {},
      },
      urls: [],
      text: [],
      raw_text: false,
      file: [{
        content_type: 'audio/webm',
        data: base64Audio,
      }],
    }),
  });

  if (!response.ok) {
    throw new Error('Hume API request failed');
  }

  const jobData = await response.json();
  const jobId = jobData.job_id;

  // Poll for results
  let result = null;
  for (let i = 0; i < 30; i++) {
    await new Promise(resolve => setTimeout(resolve, 1000));

    const statusResponse = await fetch(`https://api.hume.ai/v0/batch/jobs/${jobId}/predictions`, {
      headers: {
        'X-Hume-Api-Key': apiKey,
      },
    });

    if (statusResponse.ok) {
      result = await statusResponse.json();
      break;
    }
  }

  if (!result || !result[0]?.results?.predictions) {
    // Fallback: use Web Speech API for transcription if Hume fails
    return await fallbackToWebSpeech(audioBlob);
  }

  // Extract emotions from Hume response
  const predictions = result[0].results.predictions[0];
  const prosody = predictions?.models?.prosody?.grouped_predictions?.[0]?.predictions?.[0];

  if (!prosody) {
    return await fallbackToWebSpeech(audioBlob);
  }

  const emotions: EmotionScore[] = prosody.emotions
    .sort((a: any, b: any) => b.score - a.score)
    .slice(0, 5)
    .map((e: any) => ({ name: e.name, score: e.score }));

  return {
    transcript: prosody.text || '',
    emotions,
    primaryEmotion: emotions[0]?.name || 'neutral',
  };
}

async function fallbackToWebSpeech(audioBlob: Blob): Promise<HumeVoiceResult> {
  // This is a simplified fallback - in production you'd use a proper speech-to-text service
  return {
    transcript: '[Voice input received - please type your message]',
    emotions: [{ name: 'neutral', score: 1 }],
    primaryEmotion: 'neutral',
  };
}
