"use client"

import { useCallback, useEffect, useState } from "react"
import { CalendarDays } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

type Appointment = {
  id: number
  doctor_name: string
  scheduled_at: string
  duration_minutes: number
  visit_type: string
  status: string
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadAppointments = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/appointments`)
      if (!response.ok) throw new Error("Could not load appointments.")
      setAppointments((await response.json()) as Appointment[])
      setError("")
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load appointments.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadAppointments()
  }, [loadAppointments])

  return (
    <section className="mx-auto w-full max-w-5xl flex-1 p-4 py-8 md:p-8 md:py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Appointments</h1>
        <p className="mt-2 text-base text-muted-foreground">
          Booked visits from the appointment schedule.
        </p>
      </div>
      <div className="grid gap-4">
        {loading && appointments.length === 0 && (
          <p className="text-sm text-muted-foreground">Loading appointments…</p>
        )}
        {!loading && appointments.length === 0 && !error && (
          <p className="text-sm text-muted-foreground">No appointments booked yet.</p>
        )}
        {appointments.map((visit) => (
          <Card key={visit.id}>
            <CardContent className="flex flex-wrap items-center gap-4 p-5">
              <span className="grid size-11 place-items-center rounded-lg bg-primary/10 text-primary">
                <CalendarDays />
              </span>
              <div className="min-w-48 flex-1">
                <p className="font-medium">Dr. {visit.doctor_name}</p>
                <p className="text-sm text-muted-foreground">
                  {visit.duration_minutes} min · {visit.visit_type.replaceAll("_", " ")}
                </p>
              </div>
              <p className="text-sm font-medium">
                {new Date(visit.scheduled_at).toLocaleString()}
              </p>
              <Badge variant="outline">
                {visit.status.replaceAll("_", " ")}
              </Badge>
            </CardContent>
          </Card>
        ))}
        {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
      </div>
    </section>
  )
}
