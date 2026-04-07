import { Accordion, useThemeColor } from "heroui-native";
import { View, Text } from "react-native";

export default function MCQCompleted({
  result,
}: {
  result: Record<string, string>;
}) {
  const mutedColor = useThemeColor("muted");

  return (
    <Accordion animation="disabled" selectionMode="single" className="w-[80%]">
      <Accordion.Item value="answers">
        <Accordion.Trigger className="p-2">
          <View className="flex-row gap-2">
            <Text className="text-muted">
              Answered {Object.entries(result).length} question
              {Object.entries(result).length > 1 ? "s" : null}
            </Text>
            <Accordion.Indicator iconProps={{ color: mutedColor }} />
          </View>
        </Accordion.Trigger>

        <Accordion.Content>
          <View className="gap-2">
            {Object.entries(result).map(([key, value]) => (
              <View key={key} className="flex-row justify-between">
                <Text className="text-muted">{key}</Text>
                <Text className="text-foreground font-medium">{value}</Text>
              </View>
            ))}
          </View>
        </Accordion.Content>
      </Accordion.Item>
    </Accordion>
  );
}
