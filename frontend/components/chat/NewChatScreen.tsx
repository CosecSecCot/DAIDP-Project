import { useState } from "react";
import { Button, Spinner } from "heroui-native";
import { Keyboard, Text, View } from "react-native";
import { KeyboardAvoidingView } from "react-native-keyboard-controller";
import {
  Calendar03Icon,
  Doctor01Icon,
  MedicalFileIcon,
  PrescriptionsIcon,
} from "@hugeicons/core-free-icons";
import { useRouter } from "expo-router";
import { StyledIcon } from "@/components/icons";
import StickyChatInput from "./StickyChatInput";

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
          <KeyboardAvoidingView
            behavior="padding"
            keyboardVerticalOffset={42}
            className="flex-1 justify-center items-center gap-4"
          >
            {!isSending ? (
              <>
                <Text className="text-foreground text-2xl font-bold">
                  How can I assist you today?
                </Text>
                <View className="flex-row flex-wrap gap-2 justify-center">
                  <Button size="sm" variant="outline">
                    <StyledIcon
                      icon={Calendar03Icon}
                      size={16}
                      themeColor="accent"
                    />
                    <Button.Label>Book an appointment</Button.Label>
                  </Button>
                  <Button size="sm" variant="outline">
                    <StyledIcon
                      icon={MedicalFileIcon}
                      size={16}
                      themeColor="warning"
                    />
                    <Button.Label>Explain my report</Button.Label>
                  </Button>
                  <Button size="sm" variant="outline">
                    <StyledIcon
                      icon={PrescriptionsIcon}
                      size={16}
                      themeColor="success"
                    />
                    <Button.Label>Explain prescription</Button.Label>
                  </Button>
                  <Button size="sm" variant="outline">
                    <StyledIcon
                      icon={Doctor01Icon}
                      size={16}
                      themeColor="accent"
                    />
                    <Button.Label>Find a doctor</Button.Label>
                  </Button>
                </View>
              </>
            ) : (
              <Spinner size="lg" />
            )}
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
