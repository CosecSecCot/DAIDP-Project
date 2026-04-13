import { StyledIcon } from "@/components/icons";
import MenuScreen from "@/components/menu";
import { Add01Icon, MenuTwoLineIcon } from "@hugeicons/core-free-icons";
import { DrawerHeaderProps } from "@react-navigation/drawer";
import { useRouter } from "expo-router";
import { Drawer } from "expo-router/drawer";
import { Button } from "heroui-native";
import { Text, View } from "react-native";

export default function Layout() {
  return (
    <Drawer
      drawerContent={(props) => <MenuScreen {...props} />}
      screenOptions={{
        drawerStyle: {
          width: "100%",
        },
      }}
    >
      <Drawer.Screen
        name="index"
        options={{
          drawerLabel: "New Chat",
          title: "New Chat",
          header: (props) => <NewChatHeader {...props} />,
        }}
      />
      <Drawer.Screen
        name="chats/[chatId]"
        options={{
          header: (props) => <ChatHeader {...props} />,
        }}
      />
      <Drawer.Screen
        name="appointments/index"
        options={{
          drawerLabel: "Appointments",
          title: "Appointments",
          header: (props) => <DefaultHeader {...props} />,
        }}
      />
    </Drawer>
  );
}

function NewChatHeader(props: DrawerHeaderProps) {
  return (
    <View className="absolute top-0 w-full z-40 py-safe-offset-4 px-4 flex-row justify-between items-center">
      <Button
        size="md"
        variant="outline"
        isIconOnly
        className="bg-surface"
        onPress={() => props.navigation.openDrawer()}
      >
        <StyledIcon icon={MenuTwoLineIcon} size={28} themeColor="foreground" />
      </Button>
      <Text className="font-bold text-lg text-foreground">New Chat</Text>
    </View>
  );
}

function ChatHeader(props: DrawerHeaderProps) {
  const router = useRouter();

  return (
    <View className="bg-background pt-safe-offset-4 px-4 flex-row justify-between items-center">
      <Button
        size="md"
        variant="outline"
        isIconOnly
        className="bg-surface"
        onPress={() => props.navigation.openDrawer()}
      >
        <StyledIcon icon={MenuTwoLineIcon} size={28} themeColor="foreground" />
      </Button>
      {/* <Text className="font-bold text-lg text-foreground">
        {JSON.stringify(props.route.params)}
      </Text> */}
      <Button
        size="md"
        variant="outline"
        isIconOnly
        className="bg-surface"
        onPress={() => router.replace("/")}
      >
        <StyledIcon icon={Add01Icon} size={28} themeColor="foreground" />
      </Button>
    </View>
  );
}

function DefaultHeader(props: DrawerHeaderProps) {
  return (
    <View className="bg-background pt-safe-offset-4 px-4 flex-row justify-between items-center">
      <Button
        size="md"
        variant="outline"
        isIconOnly
        className="bg-surface"
        onPress={() => props.navigation.openDrawer()}
      >
        <StyledIcon icon={MenuTwoLineIcon} size={28} themeColor="foreground" />
      </Button>
      <Text className="font-bold text-lg text-foreground">
        {props.options.title}
      </Text>
    </View>
  );
}
