import { UserButton } from "@clerk/expo/native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { Button, ScrollShadow, Surface, TextArea } from "heroui-native";
import { Text, TextInput, View } from "react-native";
import {
  KeyboardAwareScrollView,
  KeyboardStickyView,
} from "react-native-keyboard-controller";

export default function StickyChatBoxExample() {
  return (
    <View className="flex-1 py-safe-offset-4 px-4 bg-background">
      <View className="flex-1 gap-4">
        <View className="flex-row justify-between">
          <Text className="text-foreground text-2xl font-semibold">
            AI Frontdesk
          </Text>
          <View className="h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-foreground/60">
            <UserButton />
          </View>
        </View>
        <ScrollShadow
          LinearGradientComponent={LinearGradient}
          className="h-9/10"
        >
          <KeyboardAwareScrollView showsVerticalScrollIndicator={false}>
            <Text className="mb-4 text-2xl font-bold text-foreground">
              Long Content
            </Text>
            <Text
              selectable
              className="mb-4 text-base leading-6 text-foreground"
            >
              Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
              enim ad minim veniam, quis nostrud exercitation ullamco laboris.
            </Text>
            <Text className="mb-4 text-base leading-6 text-foreground">
              Sed ut perspiciatis unde omnis iste natus error sit voluptatem
              accusantium doloremque laudantium, totam rem aperiam, eaque ipsa
              quae ab illo inventore veritatis et quasi architecto beatae vitae.
            </Text>
            <Text className="mb-4 text-base leading-6 text-foreground">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
              enim ad minim veniam, quis nostrud exercitation ullamco laboris.
            </Text>
            <Text className="mb-4 text-base leading-6 text-foreground">
              Sed ut perspiciatis unde omnis iste natus error sit voluptatem
              accusantium doloremque laudantium, totam rem aperiam, eaque ipsa
              quae ab illo inventore veritatis et quasi architecto beatae vitae.
            </Text>
            <Text className="mb-4 text-base leading-6 text-foreground">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
              enim ad minim veniam, quis nostrud exercitation ullamco laboris.
            </Text>
            <Text className="mb-4 text-base leading-6 text-foreground">
              Sed ut perspiciatis unde omnis iste natus error sit voluptatem
              accusantium doloremque laudantium, totam rem aperiam, eaque ipsa
              quae ab illo inventore veritatis et quasi architecto beatae vitae.
            </Text>
          </KeyboardAwareScrollView>
        </ScrollShadow>
      </View>
      <StickyChatInput />
    </View>
  );
}

function StickyChatInput() {
  return (
    <KeyboardStickyView
      style={{ zIndex: 100 }}
      offset={{ closed: 0, opened: 20 }}
    >
      <Surface className="flex-row justify-end gap-2 p-2 border border-separator-tertiary min-h-20">
        <TextInput
          multiline
          numberOfLines={10}
          placeholder="Ask me anything..."
          onSubmitEditing={() => console.log("submit")}
          className="flex-1 align-top"
        />
        <View className="justify-end">
          <Button size="sm" isIconOnly onPress={() => console.log("send")}>
            <Ionicons name="arrow-up" size={20} color="black" />
          </Button>
        </View>
      </Surface>
    </KeyboardStickyView>
  );
}
