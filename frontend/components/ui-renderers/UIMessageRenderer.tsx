import { UIData } from "@/types/chat";
import { Text } from "react-native";
import { Surface } from "heroui-native";
import PickerRenderer from "./PickerRenderer";
import AlertRenderer from "./AlertRenderer";

export default function UIMessageRenderer({
  ui,
  active,
  onAction,
}: {
  ui?: UIData;
  active: boolean;
  onAction: (metadata?: any) => void;
}) {
  if (!ui) return null;

  switch (ui.component) {
    case "none":
      return null;

    case "alert":
      return <AlertRenderer data={ui.data} />;

    case "picker":
      if (active) return <PickerRenderer data={ui.data} onSubmit={onAction} />;
      return null;

    default:
      return (
        <Surface>
          <Text className="text-muted text-base">
            {JSON.stringify(ui, null, 4)}
          </Text>
        </Surface>
      );
  }
}
