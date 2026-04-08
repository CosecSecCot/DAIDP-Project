import { useState } from "react";
import { Text, View } from "react-native";
import {
  Button,
  RadioGroup,
  Label,
  Radio,
  cn,
  Description,
  Card,
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
  };

  const isLast = currentIndex === questions.length - 1;
  const isFirst = currentIndex === 0;
  const selected = answers[currentQuestion.id];

  return (
    <Card className="gap-4">
      <Card.Header className="gap-2">
        {questions.length > 1 && (
          <Text className="font-semibold text-xl text-accent">
            {currentIndex + 1} / {questions.length}
          </Text>
        )}
        <Text className="font-semibold text-lg text-surface-foreground">
          {currentQuestion.text}
        </Text>
      </Card.Header>
      <Card.Body>
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
      </Card.Body>
      <Card.Footer className="gap-3">
        {!isLast ? (
          <Button isDisabled={!selected} onPress={handleNext}>
            <Button.Label>Next</Button.Label>
            <StyledIonicons
              name="chevron-forward"
              size={16}
              className="text-accent-foreground"
            />
          </Button>
        ) : (
          <Button isDisabled={!selected} onPress={handleSubmit}>
            <Button.Label>Submit</Button.Label>
            <StyledIonicons
              name="checkmark"
              size={16}
              className="text-accent-foreground"
            />
          </Button>
        )}
        {!isFirst && (
          <Button variant="ghost" onPress={handleBack}>
            <StyledIonicons
              name="chevron-back"
              size={16}
              className="text-foreground"
            />
            <Button.Label>Back</Button.Label>
          </Button>
        )}
      </Card.Footer>
    </Card>
  );
}

interface OptionItemProps {
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
}: OptionItemProps) => {
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
