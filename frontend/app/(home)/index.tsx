import { useUser } from "@clerk/expo";
import { UserButton } from "@clerk/expo/native";
import { Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function Page() {
  const { user } = useUser();

  return (
    <SafeAreaView className="flex-1 bg-neutral-900">
      <View className="absolute top-12 right-6 w-10 h-10 rounded-[18px] overflow-hidden">
        <UserButton />
      </View>
      <View className="flex-1 items-center justify-center gap-4">
        <Text className="text-white text-2xl">Welcome, {user?.firstName}!</Text>
      </View>
    </SafeAreaView>
  );
}
