import { useLocalSearchParams } from "expo-router";
import { Text, View } from "react-native";

export default function AppointmentRoute() {
  const params = useLocalSearchParams<{ appointmentId?: string | string[] }>();
  const appointmentId = parseAppointmentId(params.appointmentId);

  if (!appointmentId) {
    return null;
  }

  return (
    <View className="flex-1 justify-center items-center">
      <Text className="text-foreground">Appointment {appointmentId}</Text>
    </View>
  );
}

function parseAppointmentId(appointmentId: string | string[] | undefined) {
  if (Array.isArray(appointmentId)) {
    return Number(appointmentId[0]);
  }

  if (!appointmentId) {
    return undefined;
  }

  const parsed = Number(appointmentId);
  return Number.isFinite(parsed) ? parsed : undefined;
}
