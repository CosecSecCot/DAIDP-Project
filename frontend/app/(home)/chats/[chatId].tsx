import { useLocalSearchParams } from "expo-router";
import ChatScreen from "@/components/chat/ChatScreen";

export default function ChatRoute() {
  const params = useLocalSearchParams<{ chatId?: string | string[] }>();
  const chatId = parseChatId(params.chatId);

  if (!chatId) {
    return null;
  }

  return <ChatScreen chatId={chatId} />;
}

function parseChatId(chatId: string | string[] | undefined) {
  if (Array.isArray(chatId)) {
    return Number(chatId[0]);
  }

  if (!chatId) {
    return undefined;
  }

  const parsed = Number(chatId);
  return Number.isFinite(parsed) ? parsed : undefined;
}
