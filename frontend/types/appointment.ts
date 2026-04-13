export type Appointment = {
  id: number;
  patient_id: number;
  doctor_id: number;
  hospital_id: number;
  department_id: number;
  series_id: number;
  scheduled_at: string; // ISO date string
  duration_mins: number;
  type: string;
  status: string;
  booked_by: "patient" | "staff";
  booked_by_staff_id: number;
  notes: string;
};
