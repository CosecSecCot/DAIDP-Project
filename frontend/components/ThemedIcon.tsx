import { THEME } from "@/lib/theme";
import { type LucideIcon, type LucideProps } from "lucide-react-native";
import { useColorScheme } from "react-native";

interface ThemedIconProps extends LucideProps {
  icon: LucideIcon;
}

export default function ThemedIcon({ icon: Icon, ...props }: ThemedIconProps) {
  const colorScheme = useColorScheme();

  return (
    <Icon
      color={
        colorScheme === "dark"
          ? THEME.dark.primaryForeground
          : THEME.light.primaryForeground
      }
      {...props}
    />
  );
}
