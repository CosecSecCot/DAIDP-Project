import { useState } from "react";
import { ScrollView, Text, View } from "react-native";
import {
  Button,
  RadioGroup,
  Label,
  Radio,
  cn,
  Description,
  Card,
  ScrollShadow,
  useThemeColor,
} from "heroui-native";
import { withUniwind } from "uniwind";
import Ionicons from "@expo/vector-icons/Ionicons";
import { PickerData, PickerOption } from "@/types/chat";
import { LinearGradient } from "expo-linear-gradient";

const StyledIonicons = withUniwind(Ionicons);

export default function PickerRenderer({
  data,
  onSubmit,
}: {
  data: PickerData;
  onSubmit: (result: Record<string, string | string[]>) => void;
}) {
  const scrollGradientColor = useThemeColor("surface-secondary");

  const [selected, setSelected] = useState<string | null>(null);
  const [selectedMultiple, setSelectedMultiple] = useState<string[]>([]);

  const isMulti = data.allow_multiple;

  const handleSingleSelect = (value: string) => {
    setSelected(value);
  };

  const handleMultiToggle = (value: string) => {
    setSelectedMultiple((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value],
    );
  };

  const handleSubmit = () => {
    if (isMulti) {
      onSubmit({ values: selectedMultiple });
    } else {
      if (selected) {
        onSubmit({ value: selected });
      }
    }
  };

  const isDisabled = isMulti ? selectedMultiple.length === 0 : !selected;

  return (
    <Card className="gap-4" variant="secondary">
      {/* Header */}
      <Card.Header className="gap-2">
        <Text className="font-semibold text-lg text-surface-foreground">
          {data.title}
        </Text>
        <Text className="text-muted">{data.prompt}</Text>
      </Card.Header>

      {/* Body */}
      <Card.Body className="h-[40vh]">
        <ScrollShadow
          LinearGradientComponent={LinearGradient}
          color={scrollGradientColor}
          size={48}
          className="flex-1"
        >
          <ScrollView nestedScrollEnabled>
            {!isMulti ? (
              <RadioGroup
                value={selected ?? undefined}
                onValueChange={handleSingleSelect}
                className="gap-2"
                variant="primary"
              >
                {data.options.map((opt) => (
                  <OptionItem key={opt.value} option={opt} isMulti={false} />
                ))}
              </RadioGroup>
            ) : (
              <View className="gap-2">
                {data.options.map((opt) => {
                  const isSelected = selectedMultiple.includes(opt.value);

                  return (
                    <OptionItem
                      key={opt.value}
                      option={opt}
                      isMulti
                      isSelected={isSelected}
                      onPress={() => handleMultiToggle(opt.value)}
                    />
                  );
                })}
              </View>
            )}
          </ScrollView>
        </ScrollShadow>
      </Card.Body>

      {/* Footer */}
      <Card.Footer className="gap-3">
        <Button isDisabled={isDisabled} onPress={handleSubmit}>
          <Button.Label>Submit</Button.Label>
          <StyledIonicons
            name="checkmark"
            size={16}
            className="text-accent-foreground"
          />
        </Button>
      </Card.Footer>
    </Card>
  );
}
interface OptionItemProps {
  option: PickerOption;
  isMulti: boolean;
  isSelected?: boolean;
  onPress?: () => void;
}

const OptionItem = ({
  option,
  isMulti,
  isSelected,
  onPress,
}: OptionItemProps) => {
  if (!isMulti) {
    return (
      <RadioGroup.Item value={option.value}>
        {({ isSelected }) => (
          <View
            className={cn(
              "flex-row items-center gap-4 p-3 rounded-2xl",
              isSelected && "bg-surface-secondary",
            )}
          >
            <Radio>
              <Radio.Indicator />
            </Radio>

            <View className="flex-1">
              <Label>
                <Label.Text>{option.label}</Label.Text>
              </Label>

              {option.description && (
                <Description>{option.description}</Description>
              )}
            </View>
          </View>
        )}
      </RadioGroup.Item>
    );
  }

  // Multi-select version
  return (
    <Button
      variant={isSelected ? "primary" : "outline"}
      onPress={onPress}
      className="justify-start"
    >
      <View className="flex-1">
        <Text className="text-left">{option.label}</Text>
        {option.description && (
          <Text className="text-muted text-sm">{option.description}</Text>
        )}
      </View>
    </Button>
  );
};
