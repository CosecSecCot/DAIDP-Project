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
  AttachmentIcon,
  Mic02Icon,
  MicOff02Icon,
  MoreHorizontalIcon,
} from "@hugeicons/core-free-icons";
import { StyledIcon } from "@/components/icons";
import { useAudioSettings } from "@/context/audio-settings";
import { Dispatch, SetStateAction, useCallback, useState } from "react";
import { useSpeechToText } from "@/hooks/useSpeechToText";

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

  // Memoize to prevent hook from resetting
  const handleFinalResult = useCallback(
    (text: string) => {
      setInput((prev) => {
        const spacing = prev.length > 0 && !prev.endsWith(" ") ? " " : "";
        return `${prev}${spacing}${text}`;
      });
    },
    [setInput],
  );

  const speech = useSpeechToText({
    onFinalResult: handleFinalResult,
  });

  // Combine fixed input with live preview
  const displayValue = speech.isRecording
    ? `${input}${input && speech.transcript ? " " : ""}${speech.transcript}`
    : input;

  return (
    <KeyboardStickyView
      style={{ zIndex: 100 }}
      className="absolute bottom-0 w-full ios:p-2 ios:pb-safe-offset-0 shadow-2xl"
    >
      <View className="bg-surface gap-4 p-4 pt-3 android:pb-safe-offset-0 rounded-t-3xl ios:rounded-b-3xl ios:border ios:border-border">
        <TextInput
          multiline
          placeholder="Ask me anything..."
          value={displayValue}
          onChangeText={(text) => {
            // Prevent manual typing from clobbering the state while recording
            if (!speech.isRecording) setInput(text);
          }}
          onSubmitEditing={onSend}
          editable={!disabled && !speech.isRecording}
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
              onPress={speech.isRecording ? speech.stop : speech.start}
              isDisabled={disabled}
              className="bg-surface-secondary shadow-2xl"
            >
              <StyledIcon
                icon={speech.isRecording ? MicOff02Icon : Mic02Icon}
                size={24}
                themeColor={speech.isRecording ? "danger" : "foreground"}
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
          <ListGroup className="mb-4">
            <ListGroup.Item
              onPress={() => {
                console.log("Attached Files");
              }}
            >
              <ListGroup.ItemPrefix>
                <StyledIcon
                  icon={AttachmentIcon}
                  size={24}
                  themeColor="foreground"
                />
              </ListGroup.ItemPrefix>
              <ListGroup.ItemContent>
                <ListGroup.ItemTitle>Attach Files</ListGroup.ItemTitle>
                <ListGroup.ItemDescription>
                  Upload any files or documents
                </ListGroup.ItemDescription>
              </ListGroup.ItemContent>
            </ListGroup.Item>
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
