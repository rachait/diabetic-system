import { useEffect, useState } from "react";
import { api } from "./api";

export default function AppointmentBooking({ user }) {
  const [doctors, setDoctors] = useState([]);
  const [doctorProduct, setDoctorProduct] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ doctor_id: "", appointment_date: "", time_slot: "", appointment_type: "in-person" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() { 
      setLoading(true);
      setError("");
      try {
        const doctorRes = user?.is_admin ? await api.adminDoctors() : await api.userDoctors();
        setDoctors(doctorRes.doctors || []);
        // Add doctors as a special inventory item if present in inventory
        if (api.adminInventory) {
          const inventory = await api.adminInventory();
          const doctorItem = (inventory.products || []).find(p => p.name.toLowerCase() === "doctors");
          setDoctorProduct(doctorItem || null);
        }
        const apptRes = user?.is_admin ? await api.adminAppointments() : await api.userAppointments();
        setAppointments(apptRes.appointments || []);
      } catch (e) {
        setError(e.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    if (user) load();
  }, [user]);

  async function refreshSlots(doctor_id, date) {
    if (!doctor_id || !date) return setSlots([]);
    const res = user?.is_admin ? await api.adminAppointmentSlots(doctor_id, date) : await api.userAppointmentSlots(doctor_id, date);
    setSlots(res.slots || []);
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (!form.doctor_id || !form.appointment_date || !form.time_slot) return;
    const payload = { ...form, doctor_id: Number(form.doctor_id) };
    try {
      if (user?.is_admin) {
        await api.createAdminAppointment(payload);
      } else {
        await api.createUserAppointment(payload);
      }
      setForm({ doctor_id: "", appointment_date: "", time_slot: "", appointment_type: "in-person" });
      // reload appointments
      const apptRes = user?.is_admin ? await api.adminAppointments() : await api.userAppointments();
      setAppointments(apptRes.appointments || []);
      await refreshSlots(payload.doctor_id, payload.appointment_date);
    } catch (err) {
      setError(err.message || "Booking failed");
    }
  }

  return (
    <section className="glass rounded-3xl p-6 space-y-6">
      {error && <div className="text-red-600 font-bold">{error}</div>}
      <h3 className="text-2xl mb-4">{user?.is_admin ? "Admin Appointment Booking" : "Book an Appointment"}</h3>
      {error && <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <form onSubmit={submit} className="rounded-2xl border bg-white p-4 space-y-3">
        <select className="w-full rounded-lg border px-3 py-2" value={form.doctor_id} onChange={async (e) => { const doctor_id = e.target.value; setForm((f) => ({ ...f, doctor_id })); await refreshSlots(doctor_id, form.appointment_date); }}>
          <option value="">Select doctor</option>
          {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        {doctorProduct && (
          <div className="rounded-xl border bg-blue-50 p-3 my-2 text-blue-900">
            <strong>Doctor Consultation Available:</strong> {doctorProduct.quantity_available} slots
          </div>
        )}
        <input className="w-full rounded-lg border px-3 py-2" type="date" value={form.appointment_date} onChange={async (e) => { const appointment_date = e.target.value; setForm((f) => ({ ...f, appointment_date })); await refreshSlots(form.doctor_id, appointment_date); }} />
        <select className="w-full rounded-lg border px-3 py-2" value={form.appointment_type} onChange={(e) => setForm((f) => ({ ...f, appointment_type: e.target.value }))}>
          <option value="in-person">In-person</option>
          <option value="video call">Video</option>
        </select>
        <div className="grid grid-cols-4 gap-2 text-xs">
          {slots.map((slot) => (
            <button key={slot.time_slot} type="button" onClick={() => slot.status === "free" && setForm((f) => ({ ...f, time_slot: slot.time_slot }))} className={`rounded-lg border px-2 py-2 ${slot.status === "booked" ? "bg-slate-200 text-slate-500" : form.time_slot === slot.time_slot ? "bg-blue-600 text-white" : "bg-emerald-50 text-emerald-700"}`}>
              {slot.time_slot}
            </button>
          ))}
        </div>
        <button className="rounded-lg bg-blue-600 px-3 py-2 text-white">Book</button>
      </form>
      <div className="rounded-2xl border bg-white p-4 overflow-x-auto mt-4">
        <h4 className="font-semibold mb-2">Appointments</h4>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500"><th>Patient</th><th>Doctor</th><th>Date/time</th><th>Type</th><th>Status</th></tr></thead>
          <tbody>
            {appointments.map((row) => (
              <tr key={row.id} className="border-t">
                <td className="py-2">{row.patient_name}</td><td className="py-2">{row.doctor_name}</td><td className="py-2">{row.appointment_date} {row.time_slot}</td>
                <td className="py-2">{row.appointment_type}</td><td className="py-2">{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
