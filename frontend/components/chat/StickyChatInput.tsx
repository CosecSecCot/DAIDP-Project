import { useState } from "react";
import { Button, Spinner, Switch, useThemeColor } from "heroui-native";
import { Text, TextInput, View } from "react-native";
import { KeyboardStickyView } from "react-native-keyboard-controller";
import { ArrowUp02Icon } from "@hugeicons/core-free-icons";
import { StyledIcon } from "@/components/icons";

type StickyChatInputProps = {
  input: string;
  setInput: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
  audioEnabled?: boolean;
  onAudioEnabledChange?: (enabled: boolean) => void;
};

export default function StickyChatInput({
  input,
  setInput,
  onSend,
  disabled = false,
  audioEnabled,
  onAudioEnabledChange,
}: StickyChatInputProps) {
  const placeholderColor = useThemeColor("field-placeholder");
  const [localAudioEnabled, setLocalAudioEnabled] = useState(false);
  const isAudioEnabled = audioEnabled ?? localAudioEnabled;
  const handleAudioToggle = onAudioEnabledChange ?? setLocalAudioEnabled;

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
          <View className="flex-row items-center gap-3">
            <Switch
              isSelected={isAudioEnabled}
              onSelectedChange={handleAudioToggle}
              isDisabled={disabled}
            />
            <View className="gap-0.5">
              <Text className="text-foreground text-sm font-medium">
                Audio replies
              </Text>
              <Text className="text-foreground/60 text-xs">
                Play assistant responses automatically
              </Text>
            </View>
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
