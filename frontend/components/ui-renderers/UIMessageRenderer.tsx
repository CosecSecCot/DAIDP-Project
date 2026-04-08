import { UIData } from "@/types/chat";
import MCQBottomSheetRenderer from "./MCQRenderer";
import { Text } from "react-native";
import { Surface } from "heroui-native";
import MCQCompleted from "./MCQCompleted";

export default function UIMessageRenderer({
  ui,
  onAction,
}: {
  ui?: UIData;
  onAction: (metadata?: any) => void;
}) {
  if (!ui) return null;

  switch (ui.component) {
    case "none":
      return null;

    case "mcq":
      if (ui.state === "completed") {
        return ui.result ? <MCQCompleted result={ui.result} /> : null;
      }

      return (
        <MCQBottomSheetRenderer
          questions={ui.data.questions}
          onSubmit={onAction}
        />
      );

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
