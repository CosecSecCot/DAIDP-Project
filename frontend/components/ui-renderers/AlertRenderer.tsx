import { AlertData } from "@/types/chat";
import { Alert } from "heroui-native";

const LEVEL_TO_STATUS = {
  info: "accent",
  success: "success",
  warning: "warning",
  error: "danger",
} as const;

export default function AlertRenderer({ data }: { data: AlertData }) {
  const status = LEVEL_TO_STATUS[data.level] ?? "default";

  return (
    <Alert status={status} className="mt-2">
      <Alert.Indicator />
      <Alert.Content>
        <Alert.Title>{data.title}</Alert.Title>
        <Alert.Description>{data.message}</Alert.Description>
        {data.details && (
          <Alert.Description className="mt-1 text-xs opacity-60">
            {data.details}
          </Alert.Description>
        )}
      </Alert.Content>
    </Alert>
  );
}
