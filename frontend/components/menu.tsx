import { StyledIcon } from "@/components/icons";
import {
  Add01Icon,
  Appointment01Icon,
  ArrowLeft01Icon,
  ArrowRight01Icon,
  Cancel01Icon,
  Search01Icon,
} from "@hugeicons/core-free-icons";
import { DrawerContentComponentProps } from "@react-navigation/drawer";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import {
  Avatar,
  Button,
  ScrollShadow,
  Separator,
  Skeleton,
} from "heroui-native";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";

const CURRENT_USER_ID = 3;
const CHATS_API_URL = `https://tighter-autodidactic-cristin.ngrok-free.dev/ai-v2/chats/${CURRENT_USER_ID}`;

type ChatSession = {
  id: number;
  title: string;
  updated_at: string;
};

export default function MenuScreen(props: DrawerContentComponentProps) {
  const router = useRouter();
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [areChatsLoaded, setAreChatsLoaded] = useState(false);

  useEffect(() => {
    const loadChats = async () => {
      setAreChatsLoaded(false);

      try {
        const res = await fetch(CHATS_API_URL);

        if (!res.ok) {
          throw new Error(`Failed to load chats in menu: ${res.status}`);
        }

        const chats = (await res.json()) as ChatSession[];
        chats.sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        );

        setChats(chats);
      } catch (err) {
        console.error(err);
      } finally {
        setAreChatsLoaded(true);
      }
    };

    loadChats();
  }, [props]);

  return (
    <View className="flex-1 py-safe-offset-4 px-4 bg-background">
      <View className="flex-1">
        <View className="absolute top-0 w-full z-40 flex-row justify-between items-center">
          <Button
            size="md"
            variant="outline"
            isIconOnly
            className="bg-surface"
            onPress={() => props.navigation.closeDrawer()}
          >
            <StyledIcon icon={Cancel01Icon} size={28} themeColor="foreground" />
          </Button>
          <View className="flex-row gap-2">
            <Button
              size="md"
              variant="outline"
              className="bg-surface"
              onPress={() => router.replace("/")}
            >
              <StyledIcon icon={Add01Icon} size={20} themeColor="foreground" />
              <Button.Label>New Chat</Button.Label>
            </Button>
            <Avatar alt="user profile">
              <Avatar.Fallback>AB</Avatar.Fallback>
            </Avatar>
          </View>
        </View>

        <View className="h-[10vh]" />
        <View className="mb-4 items-start">
          <Button
            variant="tertiary"
            onPress={() => router.replace("/appointments")}
          >
            <StyledIcon
              icon={Appointment01Icon}
              size={20}
              themeColor="foreground"
            />
            <Button.Label>View Appointments</Button.Label>
          </Button>
        </View>
        <Separator className="mb-4" />
        <Text className="font-bold text-xl text-foreground mb-4">Recents</Text>

        <ScrollShadow
          LinearGradientComponent={LinearGradient}
          size={128}
          className="flex-1"
        >
          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 20 }}
          >
            <View className="gap-4">
              {areChatsLoaded
                ? [...chats, ...chats].map((chat, idx) => (
                    <Pressable
                      key={idx}
                      onPress={() => router.replace(`/chats/${chat.id}`)}
                      className="w-full flex-row gap-4 justify-between"
                    >
                      <Text className="w-3/4 text-lg text-foreground line-clamp-1">
                        {chat.title}
                      </Text>
                      <StyledIcon
                        icon={ArrowRight01Icon}
                        size={20}
                        themeColor="foreground"
                      />
                    </Pressable>
                  ))
                : Array(5)
                    .fill(0)
                    .map((_, idx) => (
                      <Skeleton
                        key={idx}
                        animation="disable-all"
                        className="w-1/4 h-6 rounded-md"
                      />
                    ))}
            </View>
          </ScrollView>
        </ScrollShadow>
      </View>
    </View>
  );
}
