import {
  BottomSheet,
  Button,
  ControlField,
  ListGroup,
  Spinner,
  useThemeColor,
} from "heroui-native";
import { TextInput, View } from "react-native";
import { KeyboardStickyView } from "react-native-keyboard-controller";
import {
  ArrowUp02Icon,
  Mic02Icon,
  MicOff02Icon,
  MoreHorizontalIcon,
} from "@hugeicons/core-free-icons";
import { StyledIcon } from "@/components/icons";
import { useAudioSettings } from "@/context/audio-settings";
import { Dispatch, SetStateAction, useCallback, useRef, useState } from "react";
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from "expo-speech-recognition";
import { useFocusEffect } from "expo-router";

type StickyChatInputProps = {
  input: string;
  setInput: Dispatch<SetStateAction<string>>;
  onSend: () => void;
  disabled?: boolean;
};

export default function StickyChatInput({
  input,
  setInput,
  onSend,
  disabled = false,
}: StickyChatInputProps) {
  const placeholderColor = useThemeColor("field-placeholder");

  const [isRecording, setIsRecording] = useState(false);
  const transcriptTallyRef = useRef("");
  const hasCommittedRef = useRef(false);

  useSpeechRecognitionEvent("start", () => {
    setIsRecording(true);
    transcriptTallyRef.current = "";
    hasCommittedRef.current = false;
  });

  useSpeechRecognitionEvent("result", (ev) => {
    const transcript = ev.results[0]?.transcript || "";

    if (ev.isFinal) {
      // ✅ Only accumulate FINAL chunks
      transcriptTallyRef.current += transcript;
    }
  });

  useSpeechRecognitionEvent("end", () => {
    setIsRecording(false);

    // ✅ Prevent duplicate commits (VERY IMPORTANT)
    if (hasCommittedRef.current) return;
    hasCommittedRef.current = true;

    const finalText = transcriptTallyRef.current.trim();

    if (finalText) {
      setInput((prev) => {
        const spacing = prev.length > 0 && !prev.endsWith(" ") ? " " : "";
        return prev + spacing + finalText;
      });
    }

    // reset
    transcriptTallyRef.current = "";
  });

  useSpeechRecognitionEvent("error", () => {
    setIsRecording(false);
    transcriptTallyRef.current = "";
  });

  const start = async () => {
    if (isRecording) return;

    const permission =
      await ExpoSpeechRecognitionModule.requestPermissionsAsync();

    if (!permission.granted) return;

    ExpoSpeechRecognitionModule.start({
      lang: "en-US",
      interimResults: true,
      continuous: false,
    });
  };

  const stop = () => {
    ExpoSpeechRecognitionModule.stop();
  };

  useFocusEffect(
    useCallback(() => {
      // when screen gains focus → reset
      setInput("");
      transcriptTallyRef.current = "";

      return () => {
        // when leaving screen → stop recognition
        ExpoSpeechRecognitionModule.abort();
        transcriptTallyRef.current = "";
      };
    }, []),
  );

  return (
    <KeyboardStickyView
      style={{ zIndex: 100 }}
      className="absolute bottom-0 w-full ios:p-2 ios:pb-safe-offset-0 shadow-2xl"
    >
      <View className="bg-surface gap-4 p-4 pt-3 android:pb-safe-offset-0 rounded-t-3xl ios:rounded-b-3xl ios:border ios:border-border">
        <TextInput
          multiline
          placeholder={isRecording ? "Recording..." : "Ask me anything or use your voice..."}
          value={input}
          onChangeText={(text) => {
            // Prevent manual typing from clobbering the state while recording
            if (!isRecording) setInput(text);
          }}
          onSubmitEditing={onSend}
          editable={!disabled && !isRecording}
          placeholderTextColor={placeholderColor}
          className="text-foreground text-base"
        />
        <View className="flex-row items-center justify-between gap-4">
          <View className="flex-row items-center gap-2">
            <SettingsSheet />
            <Button
              size="md"
              variant="outline"
              isIconOnly
              onPress={isRecording ? stop : start}
              isDisabled={disabled}
              className="bg-surface-secondary shadow-2xl"
            >
              <StyledIcon
                icon={isRecording ? MicOff02Icon : Mic02Icon}
                size={24}
                themeColor={isRecording ? "danger" : "foreground"}
              />
            </Button>
          </View>
          <Button
            size="md"
            variant="outline"
            isIconOnly
            onPress={onSend}
            isDisabled={disabled}
            className="bg-surface-secondary shadow-2xl"
          >
            {disabled ? (
              <Spinner color={placeholderColor} />
            ) : (
              <StyledIcon
                icon={ArrowUp02Icon}
                size={24}
                themeColor="foreground"
              />
            )}
          </Button>
        </View>
      </View>
    </KeyboardStickyView>
  );
}

function SettingsSheet() {
  const { audioEnabled, isLoaded, setAudioEnabled } = useAudioSettings();

  const [isOpen, setIsOpen] = useState(false);

  return (
    <BottomSheet isOpen={isOpen} onOpenChange={setIsOpen}>
      <BottomSheet.Trigger asChild>
        <Button
          size="md"
          variant="outline"
          isIconOnly
          isDisabled={isOpen}
          className="bg-surface-secondary shadow-2xl"
        >
          <StyledIcon
            icon={MoreHorizontalIcon}
            size={24}
            themeColor="foreground"
          />
        </Button>
      </BottomSheet.Trigger>
      <BottomSheet.Portal>
        <BottomSheet.Overlay />
        <BottomSheet.Content>
          <BottomSheet.Title className="text-center">Options</BottomSheet.Title>
          <ListGroup className="mb-4">
            <ControlField
              isSelected={audioEnabled}
              onSelectedChange={setAudioEnabled}
              disabled={!isLoaded}
              isDisabled={!isLoaded}
              className="flex-row items-center gap-3 py-4 px-4"
            >
              <ListGroup.ItemContent>
                <ListGroup.ItemTitle>Audio replies</ListGroup.ItemTitle>
                <ListGroup.ItemDescription>
                  Play assistant responses automatically
                </ListGroup.ItemDescription>
              </ListGroup.ItemContent>
              <ControlField.Indicator />
            </ControlField>
          </ListGroup>
          <Button
            variant="ghost"
            onPress={() => setIsOpen(false)}
            feedbackVariant="scale"
          >
            <Button.Label className="font-semibold">Dismiss</Button.Label>
          </Button>
        </BottomSheet.Content>
      </BottomSheet.Portal>
    </BottomSheet>
  );
}
