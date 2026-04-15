"use client";

import {
  Avatar,
  Card,
  Dropdown,
  Label,
  ScrollShadow,
  Drawer,
  Button,
} from "@heroui/react";
import { useEffect, useState } from "react";

const CURRENT_DOCTOR_ID = 1;
const APPOINTMENTS_API_URL = `http://localhost:8000/appointments/doctor/${CURRENT_DOCTOR_ID}`;

// ---------------- TYPES ----------------

type Appointment = {
  id: number;
  patient_id: number;
  doctor_id: number;
  hospital_id: number;
  department_id: number;
  series_id: number;
  scheduled_at: string;
  duration_mins: number;
  type: string;
  status: string;
  booked_by: "patient" | "staff";
  booked_by_staff_id: number;
  notes: string;
};

type Patient = {
  id: number;
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  phone?: string;
  email?: string;
  address?: string;
  blood_group?: string;
};

type Document = {
  id: number;
  patient_id: number;
  appointment_id?: number;
  record_id?: number;
  uploaded_by: string;
  file_name: string;
  file_url: string;
  document_type?: string;
  uploaded_at?: string;
};

// ---------------- PAGE ----------------

export default function Page() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [areAppointmentsLoaded, setAreAppointmentsLoaded] = useState(false);

  useEffect(() => {
    let isActive = true;

    const loadAppointments = async () => {
      setAreAppointmentsLoaded(false);

      try {
        const res = await fetch(APPOINTMENTS_API_URL);
        if (!res.ok) throw new Error("Failed to load appointments");

        const data = await res.json();
        if (isActive) setAppointments(data);
      } catch (err) {
        console.error(err);
      } finally {
        if (isActive) setAreAppointmentsLoaded(true);
      }
    };

    loadAppointments();
    return () => {
      isActive = false;
    };
  }, []);

  return (
    <div className="w-full min-h-screen flex flex-1 items-center justify-center">
      <main className="py-6 px-4 w-3/4">
        <div className="flex flex-row justify-between gap-4">
          <div>
            <h1 className="text-2xl">Welcome {"Jagjot Singh"}</h1>
            <p className="text-muted">
              Today: {new Date().toLocaleDateString()}
            </p>
          </div>

          <Dropdown>
            <Dropdown.Trigger>
              <Avatar>
                <Avatar.Fallback>JS</Avatar.Fallback>
              </Avatar>
            </Dropdown.Trigger>
            <Dropdown.Popover placement="bottom right">
              <Dropdown.Menu>
                <Dropdown.Item id="view-profile">
                  <Label>View Profile</Label>
                </Dropdown.Item>
                <Dropdown.Item id="logout" variant="danger">
                  <Label>Logout</Label>
                </Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown.Popover>
          </Dropdown>
        </div>

        <ScrollShadow className="mt-[10vh] max-h-[50vh] w-4/5 mx-auto pb-6">
          {areAppointmentsLoaded ? (
            appointments.map((appointment) => (
              <AppointmentCard key={appointment.id} appointment={appointment} />
            ))
          ) : (
            <div>Loading...</div>
          )}
        </ScrollShadow>
      </main>
    </div>
  );
}

// ---------------- APPOINTMENT CARD ----------------

function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  const [isOpen, setIsOpen] = useState(false);

  // documents
  const [documents, setDocuments] = useState<Document[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  // fetch patient
  useEffect(() => {
    let isActive = true;

    const fetchPatient = async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/patients/${appointment.patient_id}`,
        );
        if (!res.ok) throw new Error("Failed to fetch patient");

        const data = await res.json();
        if (isActive) setPatient(data);
      } catch (err) {
        console.error(err);
      } finally {
        if (isActive) setLoading(false);
      }
    };

    fetchPatient();
    return () => {
      isActive = false;
    };
  }, [appointment.patient_id]);

  // fetch documents when drawer opens
  useEffect(() => {
    if (!isOpen) return;

    const fetchDocs = async () => {
      setDocsLoading(true);
      try {
        const res = await fetch(
          `http://localhost:8000/appointments/patient/${appointment.patient_id}/documents`,
        );

        if (!res.ok) throw new Error("Failed to fetch docs");

        const data = await res.json();

        // 🔥 FILTER HERE
        const filtered = data.filter(
          (d: Document) => d.appointment_id === appointment.id,
        );

        setDocuments(filtered);
      } catch (err) {
        console.error(err);
      } finally {
        setDocsLoading(false);
      }
    };

    fetchDocs();
  }, [isOpen, appointment.id, appointment.patient_id]);

  const handleUpload = async (file: File) => {
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("appointment_id", String(appointment.id));
    formData.append("uploaded_by", "doctor");

    try {
      const res = await fetch(
        `http://localhost:8000/appointments/patient/${appointment.patient_id}/documents`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!res.ok) throw new Error("Upload failed");

      const newDoc = await res.json();

      if (newDoc.appointment_id === appointment.id) {
        setDocuments((prev) => [newDoc, ...prev]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    try {
      await fetch(
        `http://localhost:8000/appointments/patient/${appointment.patient_id}/documents/${docId}`,
        { method: "DELETE" },
      );

      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      console.error(err);
    }
  };

  const date = new Date(appointment.scheduled_at).toLocaleString();

  return (
    <>
      <Card
        className="mb-4 p-4 cursor-pointer hover:bg-default-100 transition"
        onClick={() => setIsOpen(true)}
      >
        <Card.Header>
          <Card.Title className="text-lg">
            {loading ? "Loading..." : patient?.full_name || "Unknown Patient"}
          </Card.Title>
          <Card.Description>{date}</Card.Description>
        </Card.Header>

        <Card.Content>
          {loading ? (
            <p>Loading patient info...</p>
          ) : (
            <div className="text-sm space-y-1">
              <p>
                <strong>Gender:</strong> {patient?.gender || "-"}
              </p>
              <p>
                <strong>Phone:</strong> {patient?.phone || "-"}
              </p>
            </div>
          )}
        </Card.Content>
      </Card>

      {/* Drawer */}
      <Drawer>
        <Drawer.Backdrop isOpen={isOpen} onOpenChange={setIsOpen}>
          <Drawer.Content placement="right">
            <Drawer.Dialog>
              <Drawer.CloseTrigger />

              <Drawer.Header>
                <Drawer.Heading>
                  {patient?.full_name || "Patient Details"}
                </Drawer.Heading>
              </Drawer.Header>

              <Drawer.Body>
                {loading ? (
                  <p>Loading...</p>
                ) : (
                  <div className="space-y-4 text-sm">
                    {/* Appointment */}
                    <div>
                      <h3 className="font-semibold">Appointment</h3>
                      <p>
                        <strong>Date:</strong> {date}
                      </p>
                      <p>
                        <strong>Type:</strong> {appointment.type}
                      </p>
                      <p>
                        <strong>Status:</strong> {appointment.status}
                      </p>
                      <p>
                        <strong>Duration:</strong> {appointment.duration_mins}{" "}
                        mins
                      </p>
                    </div>

                    {/* Patient */}
                    <div>
                      <h3 className="font-semibold">Patient Info</h3>
                      <p>
                        <strong>Gender:</strong> {patient?.gender || "-"}
                      </p>
                      <p>
                        <strong>Phone:</strong> {patient?.phone || "-"}
                      </p>
                      <p>
                        <strong>Email:</strong> {patient?.email || "-"}
                      </p>
                      <p>
                        <strong>Blood Group:</strong>{" "}
                        {patient?.blood_group || "-"}
                      </p>
                      <p>
                        <strong>Address:</strong> {patient?.address || "-"}
                      </p>
                    </div>

                    {/* Notes */}
                    {appointment.notes && (
                      <div>
                        <h3 className="font-semibold">Notes</h3>
                        <p>{appointment.notes}</p>
                      </div>
                    )}

                    {/* Documents */}
                    <div>
                      <h3 className="font-semibold">Documents</h3>

                      <input
                        type="file"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleUpload(file);
                        }}
                      />

                      {uploading && <p>Uploading...</p>}

                      {docsLoading ? (
                        <p>Loading documents...</p>
                      ) : documents.length === 0 ? (
                        <p>No documents found.</p>
                      ) : (
                        <div className="space-y-2 mt-2">
                          {documents.map((doc) => (
                            <div
                              key={doc.id}
                              className="flex justify-between items-center border p-2 rounded"
                            >
                              <a
                                href={doc.file_url}
                                target="_blank"
                                className="text-blue-600 underline text-sm"
                              >
                                {doc.file_name}
                              </a>

                              <Button
                                size="sm"
                                variant="danger"
                                onClick={() => handleDelete(doc.id)}
                              >
                                Delete
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </Drawer.Body>

              <Drawer.Footer>
                <Button slot="close" variant="secondary">
                  Close
                </Button>
              </Drawer.Footer>
            </Drawer.Dialog>
          </Drawer.Content>
        </Drawer.Backdrop>
      </Drawer>
    </>
  );
}
