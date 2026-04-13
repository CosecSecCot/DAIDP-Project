import { Text, View } from "react-native";
import { Button, cn } from "heroui-native";
import UIMessageRenderer from "../ui-renderers/UIMessageRenderer";
import { Message } from "@/types/chat";
import { StyledIcon } from "../icons";
import { VolumeHighIcon } from "@hugeicons/core-free-icons";

export default function ChatMessage({
  message,
  active,
  onAction,
}: {
  message: Message;
  active: boolean;
  onAction: (metadata?: any) => Promise<void>;
}) {
  return (
    <View
      className={cn(
        "mb-4 gap-2",
        message.role === "user" ? "items-end" : "items-start",
      )}
    >
      {/* {message.role === "assistant" && (
        <Button size="sm" variant="outline" isIconOnly>
          <StyledIcon icon={VolumeHighIcon} size={16} themeColor="muted" />
        </Button>
      )} */}
      <Text
        selectable={message.role !== "user"}
        className={cn(
          "text-foreground text-base",
          message.role === "user"
            ? "bg-surface-tertiary max-w-[90%] px-[1em] py-[.75em] rounded-3xl"
            : "",
        )}
      >
        {message.text}
      </Text>

      {/* 🔥 Dynamic UI */}
      <UIMessageRenderer ui={message.ui} onAction={onAction} active={active} />
    </View>
  );
}
