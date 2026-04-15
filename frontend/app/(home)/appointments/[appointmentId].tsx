import { useLocalSearchParams } from "expo-router";
import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Alert, Platform, ScrollView, Text, View } from "react-native";
import { Card, Spinner, Button, Chip } from "heroui-native";
import * as Linking from "expo-linking";
import * as Sharing from "expo-sharing";
import * as Clipboard from "expo-clipboard";
import { StyledIcon } from "@/components/icons";
import { Share01Icon, Share08Icon } from "@hugeicons/core-free-icons";

const CURRENT_USER_ID = 3;

const BASE_URL = "https://tighter-autodidactic-cristin.ngrok-free.dev";
const APPOINTMENTS_API_URL = `https://tighter-autodidactic-cristin.ngrok-free.dev/appointments/patient/${CURRENT_USER_ID}`;
const DOCUMENTS_API_URL = `https://tighter-autodidactic-cristin.ngrok-free.dev/appointments/patient/${CURRENT_USER_ID}/documents`;

type Appointment = {
  id: number;
  patient_id: number;
  doctor_id: number;
  hospital_id: number;
  department_id: number;
  scheduled_at: string;
  duration_mins: number;
  type: string;
  status: string;
  notes?: string;
};

type Document = {
  id: number;
  appointment_id?: number;
  file_name: string;
  file_url: string;
  document_type?: string;
  uploaded_at?: string;
};

export default function AppointmentRoute() {
  const params = useLocalSearchParams<{ appointmentId?: string | string[] }>();
  const appointmentId = parseAppointmentId(params.appointmentId);

  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useFocusEffect(
    useCallback(() => {
      let isActive = true;

      const loadData = async () => {
        setLoading(true);

        try {
          // fetch appointments
          const res = await fetch(APPOINTMENTS_API_URL);
          const allAppointments = (await res.json()) as Appointment[];

          const found = allAppointments.find((a) => a.id === appointmentId);

          // fetch documents
          const docRes = await fetch(DOCUMENTS_API_URL);
          const allDocs = (await docRes.json()) as Document[];

          const filteredDocs = allDocs.filter(
            (d) => d.appointment_id === appointmentId,
          );

          if (!isActive) return;

          setAppointment(found ?? null);
          setDocuments(filteredDocs);
        } catch (err) {
          console.error(err);
        } finally {
          if (isActive) setLoading(false);
        }
      };

      if (appointmentId) {
        loadData();
      }

      return () => {
        isActive = false;
      };
    }, [appointmentId]),
  );

  if (!appointmentId) return null;

  if (loading) {
    return (
      <View className="flex-1 bg-background justify-center items-center">
        <Spinner size="lg" />
      </View>
    );
  }

  if (!appointment) {
    return (
      <View className="flex-1 bg-background justify-center items-center">
        <Text className="text-foreground">Appointment not found</Text>
      </View>
    );
  }

  const date = new Date(appointment.scheduled_at).toLocaleString();

  return (
    <ScrollView className="flex-1 bg-background px-4 pt-4">
      {/* 🏥 Appointment Card */}
      <Card className="mb-4">
        <Card.Body className="gap-3">
          <Text className="text-lg font-bold text-foreground">
            Appointment #{appointment.id}
          </Text>

          <Text className="text-muted">
            {date} • {appointment.duration_mins} mins
          </Text>

          <View className="flex-row gap-2 flex-wrap">
            <Chip>{appointment.type}</Chip>
            <Chip color={appointment.status === "cancelled" ? "danger" : "accent"}>{appointment.status}</Chip>
          </View>

          <Text className="text-foreground">
            Hospital: #{appointment.hospital_id}
          </Text>

          <Text className="text-foreground">
            Doctor: #{appointment.doctor_id}
          </Text>

          {appointment.notes && (
            <Text className="text-muted">Notes: {appointment.notes}</Text>
          )}
        </Card.Body>
      </Card>

      {/* 📄 Documents Section */}
      <Text className="text-lg font-semibold mb-2 text-foreground">
        Documents
      </Text>

      {documents.length === 0 ? (
        <Card>
          <Card.Body>
            <Text className="text-muted">
              No documents uploaded for this appointment.
            </Text>
          </Card.Body>
        </Card>
      ) : (
        documents.map((doc) => (
          <Card key={doc.id} className="mb-3">
            <Card.Body className="gap-2">
              <Text className="font-medium text-foreground">
                {doc.file_name}
              </Text>

              {doc.document_type && (
                <Text className="text-muted">Type: {doc.document_type}</Text>
              )}

              {doc.uploaded_at && (
                <Text className="text-muted">
                  Uploaded: {new Date(doc.uploaded_at).toLocaleString()}
                </Text>
              )}
            </Card.Body>

            <Card.Footer className="mt-4 flex-row justify-end gap-2">
              <Button
                size="sm"
                variant="ghost"
                isDisabled={downloadingId === doc.id} // when downloading current document, make it disabled.
                onPress={async () => {
                  setDownloadingId(doc.id);
                  await handleShare(doc.id);
                  setDownloadingId(null);
                }}
              >
                <StyledIcon icon={Share08Icon} size={16} themeColor="foreground" />
                <Button.Label>Share</Button.Label>
              </Button>
              <Button
                size="sm"
                variant="secondary"
                isDisabled={downloadingId === doc.id} // when downloading current document, make it disabled.
                onPress={async () => {
                  setDownloadingId(doc.id);
                  await handleOpenFile(doc.id);
                  setDownloadingId(null);
                }}
              >
                <StyledIcon icon={Share01Icon} size={16} themeColor="accent" />
                <Button.Label>Open</Button.Label>
              </Button>
            </Card.Footer>
          </Card>
        ))
      )}
    </ScrollView>
  );
}

function parseAppointmentId(appointmentId: string | string[] | undefined) {
  if (Array.isArray(appointmentId)) {
    return Number(appointmentId[0]);
  }

  if (!appointmentId) return undefined;

  const parsed = Number(appointmentId);
  return Number.isFinite(parsed) ? parsed : undefined;
}

async function handleOpenFile(doc_id: number) {
  try {
    const fullUrl = `${BASE_URL}/appointments/patient/3/documents/${doc_id}/file`;
    await Linking.openURL(fullUrl);
  } catch (err) {
    console.error(err);
    Alert.alert("Error", "Failed to open file");
  }
}

async function handleShare(doc_id: number) {
  try {
    const fullUrl = `${BASE_URL}/appointments/patient/3/documents/${doc_id}/file`;

    // ❗ Sharing only works with local files properly
    const canShare = await Sharing.isAvailableAsync();

    if (Platform.OS === "web") {
      // Web → open directly
      await Linking.openURL(fullUrl);
      return;
    }

    if (!canShare) {
      // fallback → copy link
      await Clipboard.setStringAsync(fullUrl);
      Alert.alert("Link copied", "You can now paste and share it.");
      return;
    }

    // ⚠️ Try sharing URL (works on some devices, not guaranteed)
    try {
      await Sharing.shareAsync(fullUrl);
    } catch {
      // fallback → copy link
      await Clipboard.setStringAsync(fullUrl);
      Alert.alert("Link copied", "Sharing not supported, link copied instead.");
    }
  } catch (err) {
    console.error(err);
    Alert.alert("Error", "Failed to share file");
  }
}