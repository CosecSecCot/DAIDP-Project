import { Button } from "@/components/ui/button";
import { Text } from "@/components/ui/text";
import { useUser } from "@clerk/expo";
import { UserButton } from "@clerk/expo/native";
import { View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { ArrowRightIcon, PlusIcon } from "lucide-react-native";
import ThemedIcon from "@/components/ThemedIcon";

export default function Page() {
  const { user } = useUser();

  return (
    <SafeAreaView className="flex-1">
      <View className="absolute top-12 right-6 w-10 h-10 rounded-[18px] overflow-hidden">
        <UserButton />
      </View>
      <View className="flex-1 items-center justify-center gap-4">
        <Text className="text-2xl">Welcome, {user?.firstName}!</Text>
        <Button className="rounded-full">
          <Text>Get Started</Text>
          <ThemedIcon icon={ArrowRightIcon} size={18} />
        </Button>
      </View>
    </SafeAreaView>
  );
}
