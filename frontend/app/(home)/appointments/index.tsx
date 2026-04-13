import { Appointment } from "@/types/appointment";
import { useRouter } from "expo-router";
import { Button, Card, Spinner } from "heroui-native";
import { useEffect, useState } from "react";
import { Text, View } from "react-native";

const CURRENT_USER_ID = 3;
const APPOINTMENTS_API_URL = `https://tighter-autodidactic-cristin.ngrok-free.dev/appointments/patient/${CURRENT_USER_ID}`;

export default function AppointmentsRoute() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [areAppointmentsLoaded, setAreAppointmentsLoaded] = useState(false);

  useEffect(() => {
    let isActive = true;

    const loadAppointments = async () => {
      setAreAppointmentsLoaded(false);

      try {
        const res = await fetch(APPOINTMENTS_API_URL);

        if (!res.ok) {
          throw new Error(`Failed to load appointments: ${res.status}`);
        }

        const appointments = (await res.json()) as Appointment[];

        if (!isActive) return;

        setAppointments(appointments);
      } catch (err) {
        console.error(err);
      } finally {
        if (isActive) {
          setAreAppointmentsLoaded(true);
        }
      }
    };

    loadAppointments();

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <View className="flex-1 pb-safe-offset-4 pt-4 px-4 bg-background gap-4">
      {!areAppointmentsLoaded ? (
        <View className="flex-1 justify-center items-center">
          <Spinner size="lg" />
        </View>
      ) : appointments.length > 0 ? (
        appointments.map((appointment) => (
          <AppointmentCard key={appointment.id} appointment={appointment} />
        ))
      ) : (
        <View className="flex-1 justify-center items-center">
          <Text className="text-foreground">No Appointments made yet!</Text>
        </View>
      )}
    </View>
  );
}

function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const router = useRouter();

  const date = new Date(appointment.scheduled_at).toLocaleString();

  return (
    <Card>
      <View className="gap-4">
        <Card.Body className="mb-4">
          <View className="gap-1 mb-2">
            <Card.Title className="text-muted">
              {date} • {appointment.duration_mins} mins
            </Card.Title>

            <Card.Title>Hospital #{appointment.hospital_id}</Card.Title>
          </View>

          <Card.Description>
            Type: {appointment.type} | Status: {appointment.status}
          </Card.Description>
        </Card.Body>

        <Card.Footer className="gap-3 items-end">
          <Button
            variant="ghost"
            onPress={() => router.push(`/appointments/${appointment.id}`)}
          >
            <Button.Label>View Details</Button.Label>
          </Button>
        </Card.Footer>
      </View>
    </Card>
  );
}
