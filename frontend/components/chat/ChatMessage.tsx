import { Text, View } from "react-native";
import { cn } from "heroui-native";
import UIMessageRenderer from "../ui-renderers/UIMessageRenderer";
import { Message } from "@/types/chat";

export default function ChatMessage({
  message,
  onAction,
}: {
  message: Message;
  onAction: (metadata?: any) => void;
}) {
  return (
    <View
      className={cn(
        "mb-4 gap-2",
        message.role === "user" ? "items-end" : "items-start",
      )}
    >
      <Text
        selectable={message.role !== "user"}
        className={cn(
          "text-foreground text-base",
          message.role === "user"
            ? "bg-surface-tertiary max-w-[80%] px-[1em] py-[.75em] rounded-3xl"
            : "",
        )}
      >
        {message.text}
      </Text>

      {/* 🔥 Dynamic UI */}
      <UIMessageRenderer ui={message.ui} onAction={onAction} />
    </View>
  );
}
