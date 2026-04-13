import { useCallback, useEffect, useRef, useState } from "react";
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from "expo-speech-recognition";

type UseSpeechToTextOptions = {
  onFinalResult: (text: string) => void;
};

export function useSpeechToText({ onFinalResult }: UseSpeechToTextOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");

  // We use a ref to track the transcript so the "end" event
  // always sees the most recent version without causing render loops.
  const transcriptRef = useRef("");
  const isStartingRef = useRef(false);
  const isMountedRef = useRef(true);

  useSpeechRecognitionEvent("start", () => {
    setIsRecording(true);
    isStartingRef.current = false;
  });

  useSpeechRecognitionEvent("end", () => {
    if (!isMountedRef.current) return;

    setIsRecording(false);
    isStartingRef.current = false;

    // Send the final result only once when the session ends
    const finalResult = transcriptRef.current.trim();
    if (finalResult) {
      onFinalResult(finalResult);
    }

    // Reset for next time
    transcriptRef.current = "";
    setLiveTranscript("");
  });

  useSpeechRecognitionEvent("result", (event) => {
    if (!isMountedRef.current) return;

    const text = event.results.map((r) => r.transcript).join(" ");
    transcriptRef.current = text;
    setLiveTranscript(text); // For the UI preview
  });

  useSpeechRecognitionEvent("error", (event) => {
    setIsRecording(false);
    isStartingRef.current = false;
    transcriptRef.current = "";
    setLiveTranscript("");
    console.error("Speech Error:", event.error, event.message);
  });

  const start = useCallback(async () => {
    if (isStartingRef.current || isRecording) return;
    isStartingRef.current = true;

    try {
      const permission =
        await ExpoSpeechRecognitionModule.requestPermissionsAsync();
      if (!permission.granted) {
        isStartingRef.current = false;
        return;
      }

      setLiveTranscript("");
      transcriptRef.current = "";

      ExpoSpeechRecognitionModule.start({
        lang: "en-US",
        interimResults: true,
        continuous: false, // Auto-stops when you stop speaking
      });
    } catch (err) {
      isStartingRef.current = false;
      setIsRecording(false);
    }
  }, [isRecording]);

  const stop = useCallback(() => {
    ExpoSpeechRecognitionModule.stop();
  }, []);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      ExpoSpeechRecognitionModule.abort();
    };
  }, []);

  return {
    start,
    stop,
    isRecording,
    transcript: liveTranscript,
  };
}
