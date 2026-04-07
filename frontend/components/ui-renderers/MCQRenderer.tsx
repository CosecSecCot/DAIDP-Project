import { useState } from "react";
import { Text, View } from "react-native";
import {
  BottomSheet,
  Button,
  RadioGroup,
  Label,
  Radio,
  cn,
  Description,
} from "heroui-native";
import { MCQQuestion } from "@/types/chat";
import { withUniwind } from "uniwind";
import Ionicons from "@expo/vector-icons/Ionicons";

const StyledIonicons = withUniwind(Ionicons);

export default function MCQBottomSheetRenderer({
  questions,
  onSubmit,
}: {
  questions: MCQQuestion[];
  onSubmit: (answers: Record<string, string>) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const currentQuestion = questions[currentIndex];

  const handleSelect = (option: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: option,
    }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleSubmit = () => {
    onSubmit(answers); // 🔥 send metadata
    setIsOpen(false);
  };

  const isLast = currentIndex === questions.length - 1;
  const isFirst = currentIndex === 0;
  const selected = answers[currentQuestion.id];

  return (
    <BottomSheet isOpen={isOpen} onOpenChange={setIsOpen}>
      <BottomSheet.Trigger asChild>
        <Button size="sm" variant="outline">
          Answer Question
        </Button>
      </BottomSheet.Trigger>
      <BottomSheet.Portal>
        <BottomSheet.Overlay />

        <BottomSheet.Content>
          <View className="mb-8 gap-2 items-center">
            <BottomSheet.Title className="text-center">
              {currentQuestion.text}
            </BottomSheet.Title>
            {/* <BottomSheet.Description className="text-center"></BottomSheet.Description> */}
          </View>
          <View className="mb-8 gap-2">
            <RadioGroup
              value={selected}
              onValueChange={handleSelect}
              className="gap-2"
              variant="secondary"
            >
              {currentQuestion.options.map((opt) => (
                <OptionItem key={opt} value={opt} label={opt} />
              ))}
            </RadioGroup>
          </View>
          <View className="gap-3">
            {!isFirst && (
              <Button variant="secondary" onPress={handleBack}>
                Back
              </Button>
            )}
            {!isLast ? (
              <Button isDisabled={!selected} onPress={handleNext}>
                Next
              </Button>
            ) : (
              <Button isDisabled={!selected} onPress={handleSubmit}>
                Submit
              </Button>
            )}
            <Button variant="ghost" onPress={() => setIsOpen(false)}>
              Cancel
            </Button>
          </View>
        </BottomSheet.Content>
      </BottomSheet.Portal>
    </BottomSheet>
  );
}

interface ShippingOptionItemProps {
  /** The value for the radio item */
  value: string;
  /** The label text */
  label: string;
  /** The description text */
  description?: string;
  /** Optional className for the container */
  containerClassName?: string;
  /** Optional className for the indicator */
  indicatorClassName?: string;
}

/**
 * Reusable shipping option item component for RadioGroup
 * Displays a radio option with indicator, label, description, and price
 */
const OptionItem = ({
  value,
  label,
  description,
  containerClassName,
  indicatorClassName,
}: ShippingOptionItemProps) => {
  return (
    <RadioGroup.Item value={value}>
      {({ isSelected }) => (
        <View
          className={cn(
            "flex-row items-center justify-between gap-4 p-3 rounded-2xl bg-transparent",
            isSelected && "bg-surface-secondary shadow-surface-secondary",
            containerClassName,
          )}
        >
          <Radio>
            <Radio.Indicator
              className={cn(
                !isSelected && "border border-muted/10",
                indicatorClassName,
              )}
            />
          </Radio>
          <View className="flex-1">
            <Label>
              <Label.Text maxFontSizeMultiplier={1.4}>{label}</Label.Text>
            </Label>
            {description && (
              <Description maxFontSizeMultiplier={1.4}>
                {description}
              </Description>
            )}
          </View>
        </View>
      )}
    </RadioGroup.Item>
  );
};
