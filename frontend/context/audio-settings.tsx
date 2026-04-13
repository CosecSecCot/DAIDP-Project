import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as SecureStore from "expo-secure-store";

const AUDIO_ENABLED_KEY = "chat.audio_enabled";

type AudioSettingsContextValue = {
  audioEnabled: boolean;
  isLoaded: boolean;
  setAudioEnabled: (enabled: boolean) => void;
};

const AudioSettingsContext = createContext<AudioSettingsContextValue | null>(
  null,
);

export function AudioSettingsProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [audioEnabled, setAudioEnabledState] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      try {
        const stored = await SecureStore.getItemAsync(AUDIO_ENABLED_KEY);
        if (!isActive) return;
        setAudioEnabledState(stored === "true");
      } catch (err) {
        console.error(err);
      } finally {
        if (isActive) {
          setIsLoaded(true);
        }
      }
    };

    void load();

    return () => {
      isActive = false;
    };
  }, []);

  const setAudioEnabled = (enabled: boolean) => {
    setAudioEnabledState(enabled);
    void SecureStore.setItemAsync(AUDIO_ENABLED_KEY, String(enabled)).catch(
      (err) => {
        console.error(err);
      },
    );
  };

  return (
    <AudioSettingsContext.Provider
      value={{ audioEnabled, isLoaded, setAudioEnabled }}
    >
      {children}
    </AudioSettingsContext.Provider>
  );
}

export function useAudioSettings() {
  const context = useContext(AudioSettingsContext);
  if (!context) {
    throw new Error(
      "useAudioSettings must be used within an AudioSettingsProvider",
    );
  }

  return context;
}
