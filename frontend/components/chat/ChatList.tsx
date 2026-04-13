import {
  KeyboardAvoidingView,
  KeyboardAwareScrollView,
} from "react-native-keyboard-controller";
import { ScrollShadow } from "heroui-native";
import { LinearGradient } from "expo-linear-gradient";
import ChatMessage from "./ChatMessage";
import { View } from "react-native";
import { Message } from "@/types/chat";

export default function ChatList({
  messages,
  onAction,
}: {
  messages: Message[];
  onAction: (metadata?: any) => Promise<void>;
}) {
  return (
    <ScrollShadow
      LinearGradientComponent={LinearGradient}
      size={128}
      className="flex-1 mb-[10vh]"
    >
      <KeyboardAwareScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 20 }}
      >
        <View className="h-[10vh]" />
        {messages.map((msg, index) => {
          return (
            <ChatMessage
              key={index}
              message={msg}
              onAction={onAction}
              active={index === messages.length - 1}
            />
          );
        })}
      </KeyboardAwareScrollView>
    </ScrollShadow>
  );
}
