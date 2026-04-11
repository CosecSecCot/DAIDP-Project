import { useState } from "react";
import { Button, useThemeColor } from "heroui-native";
import { Keyboard, Text, TextInput, View } from "react-native";
import {
  KeyboardAvoidingView,
  KeyboardStickyView,
} from "react-native-keyboard-controller";
import {
  Add01Icon,
  ArrowUp02Icon,
  MenuTwoLineIcon,
} from "@hugeicons/core-free-icons";
import { useRouter } from "expo-router";
import { StyledIcon } from "@/components/icons";

const CHAT_API_URL =
  "https://tighter-autodidactic-cristin.ngrok-free.dev/ai-v2/chat";
const CURRENT_USER_ID = 3;

export default function NewChatScreen() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isSending) return;

    const userMessage = input;
    setIsSending(true);
    setInput("");
    Keyboard.dismiss();

    try {
      const res = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: CURRENT_USER_ID,
          message: userMessage,
        }),
      });

      const data = await res.json();
      const nextChatId = data.chat_id as number;
      router.replace(`/chats/${nextChatId}`);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <>
      <View className="flex-1 py-safe-offset-4 px-4 bg-background">
        <View className="flex-1 gap-8">
          <View className="absolute top-0 w-full z-40 flex-row justify-between items-center">
            <Button
              size="md"
              variant="outline"
              isIconOnly
              className="bg-surface"
            >
              <StyledIcon
                icon={MenuTwoLineIcon}
                size={28}
                themeColor="foreground"
              />
            </Button>
            <Text className="font-bold text-lg text-foreground">New Chat</Text>
            <View className="w-8" />
          </View>

          <KeyboardAvoidingView
            behavior="padding"
            keyboardVerticalOffset={42}
            className="flex-1 justify-center items-center gap-2"
          >
            <Text className="text-foreground text-2xl font-bold">
              What can I help with?
            </Text>
            <Text className="text-muted text-base">
              Start by asking anything in the chat.
            </Text>
          </KeyboardAvoidingView>
        </View>
      </View>
      <StickyChatInput
        input={input}
        setInput={setInput}
        onSend={sendMessage}
        disabled={isSending}
      />
    </>
  );
}

function StickyChatInput({
  input,
  setInput,
  onSend,
  disabled = false,
}: {
  input: string;
  setInput: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
}) {
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
        <View className="items-end">
          <Button
            size="md"
            variant="outline"
            isIconOnly
            onPress={onSend}
            isDisabled={disabled}
            className="bg-surface-secondary shadow-2xl"
          >
            <StyledIcon
              icon={ArrowUp02Icon}
              size={24}
              themeColor="foreground"
            />
          </Button>
        </View>
      </View>
    </KeyboardStickyView>
  );
}
