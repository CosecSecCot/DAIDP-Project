import { useEffect, useState } from "react";
import { Button, useThemeColor } from "heroui-native";
import { Keyboard, TextInput, View } from "react-native";
import { KeyboardStickyView } from "react-native-keyboard-controller";
import {
  Add01Icon,
  ArrowUp02Icon,
  MenuTwoLineIcon,
} from "@hugeicons/core-free-icons";
import { useRouter } from "expo-router";
import { StyledIcon } from "@/components/icons";
import ChatList from "@/components/chat/ChatList";
import { Message, UIData } from "@/types/chat";

const CURRENT_USER_ID = 3;
const CHAT_API_URL =
  "https://tighter-autodidactic-cristin.ngrok-free.dev/ai-v2/chat";
const CHAT_HISTORY_API_URL = `https://tighter-autodidactic-cristin.ngrok-free.dev/ai-v2/history/${CURRENT_USER_ID}`;

export default function ChatScreen({ chatId }: { chatId: number }) {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    let isActive = true;

    const loadHistory = async () => {
      setIsHistoryLoaded(false);

      try {
        const res = await fetch(`${CHAT_HISTORY_API_URL}?chat_id=${chatId}`);

        if (!res.ok) {
          throw new Error(`Failed to load chat history: ${res.status}`);
        }

        const history = (await res.json()) as {
          role: string;
          content: unknown;
          ui?: UIData;
        }[];

        if (!isActive) return;

        setMessages(history.map(normalizeHistoryMessage));
      } catch (err) {
        console.error(err);
      } finally {
        if (isActive) {
          setIsHistoryLoaded(true);
        }
      }
    };

    loadHistory();

    return () => {
      isActive = false;
    };
  }, [chatId]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;

    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
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
          chat_id: chatId,
          message: userMessage,
        }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.message, ui: data.ui },
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  const sendAction = async (metadata: any) => {
    if (!chatId) return;

    try {
      const res = await fetch(CHAT_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: CURRENT_USER_ID,
          chat_id: chatId,
          message: metadata,
        }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.message, ui: data.ui },
      ]);
    } catch (err) {
      console.error(err);
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
            <Button
              size="md"
              variant="outline"
              isIconOnly
              className="bg-surface"
              onPress={() => router.replace("/")}
            >
              <StyledIcon icon={Add01Icon} size={28} themeColor="foreground" />
            </Button>
          </View>

          <ChatList messages={messages} onAction={sendAction} />
        </View>
      </View>
      <StickyChatInput
        input={input}
        setInput={setInput}
        onSend={sendMessage}
        disabled={!isHistoryLoaded || isSending}
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

function normalizeHistoryMessage(message: {
  role: string;
  content: unknown;
  ui?: UIData;
}): Message {
  if (message.role === "assistant") {
    const content =
      typeof message.content === "object" && message.content !== null
        ? (message.content as { message?: unknown; ui?: UIData })
        : undefined;

    return {
      role: "assistant",
      text:
        typeof content?.message === "string"
          ? content.message
          : typeof message.content === "string"
            ? message.content
            : JSON.stringify(message.content ?? ""),
      ui: content?.ui ?? message.ui,
    };
  }

  return {
    role: "user",
    text:
      typeof message.content === "string"
        ? message.content
        : JSON.stringify(message.content ?? ""),
  };
}
