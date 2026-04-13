import {
  BottomSheet,
  Button,
  ControlField,
  ListGroup,
  Spinner,
  Switch,
  useThemeColor,
} from "heroui-native";
import { Text, TextInput, View } from "react-native";
import { KeyboardStickyView } from "react-native-keyboard-controller";
import { ArrowUp02Icon, MoreHorizontalIcon } from "@hugeicons/core-free-icons";
import { StyledIcon } from "@/components/icons";
import { useAudioSettings } from "@/context/audio-settings";
import { useState } from "react";

type StickyChatInputProps = {
  input: string;
  setInput: (v: string) => void;
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

  return (
    <KeyboardStickyView
      style={{ zIndex: 100 }}
      className="absolute bottom-0 w-full ios:p-2 ios:pb-safe-offset-0 shadow-2xl"
    >
      <View className="bg-surface gap-4 p-4 pt-3 android:pb-safe-offset-0 rounded-t-3xl ios:rounded-b-3xl ios:border ios:border-border">
        <TextInput
          multiline
          placeholder="Ask me anything..."
          value={input}
          onChangeText={setInput}
          onSubmitEditing={onSend}
          editable={!disabled}
          placeholderTextColor={placeholderColor}
          className="text-foreground text-base"
        />
        <View className="flex-row items-center justify-between gap-4">
          <SettingsSheet />
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
          <ListGroup>
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
        </BottomSheet.Content>
      </BottomSheet.Portal>
    </BottomSheet>
  );
}
