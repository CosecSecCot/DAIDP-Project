import { useState } from "react";
import { UserButton } from "@clerk/expo/native";
import { Button, Surface } from "heroui-native";
import { Keyboard, Platform, Text, TextInput, View } from "react-native";
import {
  KeyboardAvoidingView,
  KeyboardStickyView,
} from "react-native-keyboard-controller";
import ChatList from "@/components/chat/ChatList";
import { UI_STATE_HANDLERS } from "@/components/ui-renderers/uiStateHandlers";
import { Message } from "@/types/chat";
import { withUniwind } from "uniwind";
import Ionicons from "@expo/vector-icons/Ionicons";

const StyledIonicons = withUniwind(Ionicons);

export default function StickyChatInputExample() {
  const [messages, setMessages] = useState<Message[]>([]);

  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;

    // add user message
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setInput("");
    Keyboard.dismiss();

    try {
      const res = await fetch(
        "https://tighter-autodidactic-cristin.ngrok-free.dev/ai/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: 1,
            message: userMessage,
            metadata: {},
          }),
        },
      );

      const data = await res.json();

      // add assistant message
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.message, ui: data.ui },
      ]);
    } catch (err) {
      console.error(err);
    }
  };

  const sendAction = async (metadata: any) => {
    setMessages((prev) =>
      prev.map((msg) => {
        const ui = msg.ui;

        console.log("HANDLING: ", JSON.stringify(ui, null, 2));

        if (!ui || ui.component === "none" || ui.state === "completed")
          return msg;

        const handler = UI_STATE_HANDLERS[ui.component];
        if (!handler) return msg;

        const res = {
          ...msg,
          ui: handler(ui, metadata),
        };

        console.log("HANDLED: ", JSON.stringify(res, null, 2));

        return res;
      }),
    );

    try {
      const res = await fetch(
        "https://tighter-autodidactic-cristin.ngrok-free.dev/ai/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: 1,
            message: "user_action", // 👈 placeholder
            metadata, // 👈 actual payload
          }),
        },
      );

      const data = await res.json();

      // ❗ ONLY assistant message added
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.message, ui: data.ui },
      ]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <View className="flex-1 py-safe-offset-4 px-4 bg-background">
      <View className="flex-1 gap-8">
        {/* Header */}
        <View className="absolute top-0 w-full z-40 flex-row justify-between items-center">
          <Button size="md" variant="outline" isIconOnly className="bg-surface">
            <StyledIonicons
              name="reorder-two"
              size={28}
              className="text-overlay-foreground"
            />
          </Button>
          <View className="h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-foreground/60">
            <UserButton />
          </View>
        </View>

        {/* Chat */}
        {messages.length > 0 ? (
          <ChatList messages={messages} onAction={sendAction} />
        ) : (
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
        )}
      </View>

      <StickyChatInput input={input} setInput={setInput} onSend={sendMessage} />
    </View>
  );
}

function StickyChatInput({
  input,
  setInput,
  onSend,
}: {
  input: string;
  setInput: (v: string) => void;
  onSend: () => void;
}) {
  return (
    <KeyboardStickyView
      style={{ zIndex: 100 }}
      offset={{ closed: Platform.OS === "ios" ? 20 : 0, opened: 20 }}
    >
      <Surface className="flex-row justify-end gap-2 p-2 border border-accent-soft min-h-20">
        <TextInput
          multiline
          placeholder="Ask me anything..."
          value={input}
          onChangeText={setInput}
          onSubmitEditing={onSend}
          className="flex-1 align-top text-foreground text-base p-2"
        />
        <View className="justify-end">
          <Button size="sm" isIconOnly onPress={onSend}>
            <StyledIonicons
              name="arrow-up"
              size={20}
              className="text-accent-foreground"
            />
          </Button>
        </View>
      </Surface>
    </KeyboardStickyView>
  );
}
