import React from "react";
import { HugeiconsIcon, HugeiconsProps } from "@hugeicons/react-native";
import { useThemeColor, ThemeColor } from "heroui-native";
import Svg from "react-native-svg";

type StyledIconProps = HugeiconsProps &
  React.RefAttributes<Svg> & {
    themeColor?: ThemeColor;
  };

export function StyledIcon({ color, themeColor, ...props }: StyledIconProps) {
  // Resolve theme color (if provided)
  const resolvedThemeColor = themeColor ? useThemeColor(themeColor) : undefined;

  // Priority: explicit themeColor > color
  const finalColor = resolvedThemeColor ?? color;

  return <HugeiconsIcon {...props} color={finalColor} />;
}
