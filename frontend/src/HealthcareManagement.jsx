import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const PRODUCT_CATEGORIES = ["Monitoring", "Supplements", "Medication", "Diet & Nutrition", "Fitness", "Services", "Doctors"];

const inr = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const todayIso = () => new Date().toISOString().slice(0, 10);

const defaultDoctor = { name: "", specialization: "", available_days: [], consultation_fee: "", status: "available" };
const defaultBooking = { patient_name: "", doctor_id: "", appointment_date: todayIso(), time_slot: "", appointment_type: "in-person", status: "confirmed" };
const defaultProduct = { name: "", category: "Monitoring", price: "", quantity_available: "", stock_threshold: 10 };

export default function HealthcareManagement({ user }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [doctorsData, setDoctorsData] = useState({ doctors: [], metrics: null });
  const [appointmentsData, setAppointmentsData] = useState({ appointments: [], summary: null });
  const [inventoryData, setInventoryData] = useState({ products: [], metrics: null });
  const [ordersData, setOrdersData] = useState({ orders: [], metrics: null });
  const [userDoctors, setUserDoctors] = useState([]);
  const [userAppointments, setUserAppointments] = useState([]);
  const [userOrders, setUserOrders] = useState([]);
  const [slotGrid, setSlotGrid] = useState([]);
  const [doctorForm, setDoctorForm] = useState(defaultDoctor);
  const [doctorEditId, setDoctorEditId] = useState(null);
  const [bookingForm, setBookingForm] = useState(defaultBooking);
  const [productForm, setProductForm] = useState(defaultProduct);
  const [productEditId, setProductEditId] = useState(null);
  const isAdmin = Boolean(user?.is_admin);

  async function loadAdminData() {
    setLoading(true);
    setError("");
    try {
      const [doctors, appointments, inventory, orders] = await Promise.all([
        api.adminDoctors(),
        api.adminAppointments(todayIso()),
        api.adminInventory(),
        api.adminOrders(),
      ]);
      setDoctorsData(doctors);
      setAppointmentsData(appointments);
      setInventoryData(inventory);
      setOrdersData(orders);
    } catch (e) {
      setError(e.message || "Failed loading admin management data.");
    } finally {
      setLoading(false);
    }
  }

  async function loadUserData() {
    setLoading(true);
    setError("");
    try {
      const [doctors, appointments, orders] = await Promise.all([api.userDoctors(), api.userAppointments(), api.userOrders()]);
      setUserDoctors(doctors.doctors || []);
      setUserAppointments(appointments.appointments || []);
      setUserOrders(orders.orders || []);
    } catch (e) {
      setError(e.message || "Failed loading user healthcare data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    if (isAdmin) {
      void loadAdminData();
    } else {
      void loadUserData();
    }
  }, [user, isAdmin]);

  async function refreshSlots(nextDoctorId, nextDate, forAdmin = true) {
    if (!nextDoctorId || !nextDate) return setSlotGrid([]);
    try {
      const data = forAdmin
        ? await api.adminAppointmentSlots(nextDoctorId, nextDate)
        : await api.userAppointmentSlots(nextDoctorId, nextDate);
      setSlotGrid(data.slots || []);
    } catch {
      setSlotGrid([]);
    }
  }

  async function submitDoctor(event) {
    event.preventDefault();
    const payload = { ...doctorForm, consultation_fee: Number(doctorForm.consultation_fee || 0) };
    if (!payload.name || !payload.specialization) return;
    await (doctorEditId ? api.updateDoctor(doctorEditId, payload) : api.createDoctor(payload));
    setDoctorForm(defaultDoctor);
    setDoctorEditId(null);
    await loadAdminData();
  }

  async function submitBooking(event) {
    event.preventDefault();
    if (!bookingForm.doctor_id || !bookingForm.time_slot || !bookingForm.appointment_date) return;
    const payload = {
      ...bookingForm,
      doctor_id: Number(bookingForm.doctor_id),
      appointment_type: bookingForm.appointment_type,
    };
    if (isAdmin) {
      await api.createAdminAppointment(payload);
      await loadAdminData();
    } else {
      await api.createUserAppointment(payload);
      await loadUserData();
    }
    setBookingForm((prev) => ({ ...prev, time_slot: "" }));
    await refreshSlots(payload.doctor_id, payload.appointment_date, isAdmin);
  }

  async function submitProduct(event) {
    event.preventDefault();
    const payload = {
      ...productForm,
      price: Number(productForm.price || 0),
      quantity_available: Number(productForm.quantity_available || 0),
      stock_threshold: Number(productForm.stock_threshold || 0),
    };
    await (productEditId ? api.updateInventoryProduct(productEditId, payload) : api.createInventoryProduct(payload));
    setProductForm(defaultProduct);
    setProductEditId(null);
    await loadAdminData();
  }

  const lowStockAlert = useMemo(() => {
    const m = inventoryData.metrics;
    if (!m) return "";
    if (m.out_of_stock_count > 0) return `${m.out_of_stock_count} products are out of stock.`;
    if (m.low_stock_count > 0) return `${m.low_stock_count} products are below threshold.`;
    return "";
  }, [inventoryData.metrics]);

  if (!user) return null;

  return (
    <section className="glass rounded-3xl p-6 space-y-6">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-2xl">{isAdmin ? "Healthcare Admin Management" : "My Healthcare Services"}</h3>
        <button className="rounded-xl border border-slate-300 px-3 py-2 text-sm" onClick={() => (isAdmin ? loadAdminData() : loadUserData())} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      {isAdmin ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Total doctors" value={doctorsData.metrics?.total_doctors || 0} />
            <Metric label="Available today" value={doctorsData.metrics?.available_today || 0} />
            <Metric label="Appointments today" value={doctorsData.metrics?.appointments_today || 0} />
            <Metric label="Average rating" value={doctorsData.metrics?.average_rating || 0} />
          </div>

          <TwoCol>
            <form onSubmit={submitDoctor} className="rounded-2xl border bg-white p-4 space-y-3">
              <h4 className="font-semibold">{doctorEditId ? "Edit doctor" : "Add doctor"}</h4>
              <input className="w-full rounded-lg border px-3 py-2" placeholder="Name" value={doctorForm.name} onChange={(e) => setDoctorForm((p) => ({ ...p, name: e.target.value }))} />
              <input className="w-full rounded-lg border px-3 py-2" placeholder="Specialization" value={doctorForm.specialization} onChange={(e) => setDoctorForm((p) => ({ ...p, specialization: e.target.value }))} />
              <input className="w-full rounded-lg border px-3 py-2" placeholder="Consultation fee (INR)" type="number" value={doctorForm.consultation_fee} onChange={(e) => setDoctorForm((p) => ({ ...p, consultation_fee: e.target.value }))} />
              <select className="w-full rounded-lg border px-3 py-2" value={doctorForm.status} onChange={(e) => setDoctorForm((p) => ({ ...p, status: e.target.value }))}>
                <option value="available">Available</option>
                <option value="busy">Busy</option>
              </select>
              <div className="flex flex-wrap gap-2 text-xs">
                {DAYS.map((day) => (
                  <button key={day} type="button" className={`rounded-full border px-2 py-1 ${doctorForm.available_days.includes(day) ? "bg-blue-600 text-white" : ""}`} onClick={() => setDoctorForm((p) => ({ ...p, available_days: p.available_days.includes(day) ? p.available_days.filter((d) => d !== day) : [...p.available_days, day] }))}>
                    {day}
                  </button>
                ))}
              </div>
              <button className="rounded-lg bg-blue-600 px-3 py-2 text-white">{doctorEditId ? "Update" : "Add"}</button>
            </form>

            <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
              <h4 className="font-semibold mb-2">Doctor table</h4>
              <table className="w-full text-sm">
                <thead><tr className="text-left text-slate-500"><th>Name</th><th>Specialization</th><th>Slots</th><th>Status</th><th /></tr></thead>
                <tbody>
                  {(doctorsData.doctors || []).map((doctor) => (
                    <tr key={doctor.id} className="border-t">
                      <td className="py-2"><span className="mr-2 inline-grid h-8 w-8 place-content-center rounded-full bg-slate-100 font-semibold">{doctor.initials}</span>{doctor.name}</td>
                      <td className="py-2"><span className="rounded-full border bg-cyan-50 px-2 py-1 text-xs">{doctor.specialization}</span></td>
                      <td className="py-2">{doctor.slot_count ?? 0}</td>
                      <td className="py-2"><span className={`rounded-full px-2 py-1 text-xs ${doctor.status === "available" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{doctor.status}</span></td>
                      <td className="py-2 space-x-2">
                        <button className="rounded border px-2 py-1" onClick={() => { setDoctorEditId(doctor.id); setDoctorForm({ name: doctor.name, specialization: doctor.specialization, consultation_fee: doctor.consultation_fee, available_days: doctor.available_days || [], status: doctor.status }); }}>Edit</button>
                        <button className="rounded border border-red-300 px-2 py-1 text-red-700" onClick={async () => { await api.deleteDoctor(doctor.id); await loadAdminData(); }}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TwoCol>

          <TwoCol>
            <form onSubmit={submitBooking} className="rounded-2xl border bg-white p-4 space-y-3">
              <h4 className="font-semibold">Create appointment booking</h4>
              <input className="w-full rounded-lg border px-3 py-2" placeholder="Patient name" value={bookingForm.patient_name} onChange={(e) => setBookingForm((p) => ({ ...p, patient_name: e.target.value }))} />
              <select className="w-full rounded-lg border px-3 py-2" value={bookingForm.doctor_id} onChange={async (e) => { const doctor_id = e.target.value; setBookingForm((p) => ({ ...p, doctor_id })); await refreshSlots(doctor_id, bookingForm.appointment_date, true); }}>
                <option value="">Select doctor</option>
                {(doctorsData.doctors || []).map((doctor) => <option key={doctor.id} value={doctor.id}>{doctor.name}</option>)}
              </select>
              <input className="w-full rounded-lg border px-3 py-2" type="date" value={bookingForm.appointment_date} onChange={async (e) => { const appointment_date = e.target.value; setBookingForm((p) => ({ ...p, appointment_date })); await refreshSlots(bookingForm.doctor_id, appointment_date, true); }} />
              <select className="w-full rounded-lg border px-3 py-2" value={bookingForm.appointment_type} onChange={(e) => setBookingForm((p) => ({ ...p, appointment_type: e.target.value }))}>
                <option value="in-person">In-person</option>
                <option value="video call">Video</option>
              </select>
              <select className="w-full rounded-lg border px-3 py-2" value={bookingForm.status} onChange={(e) => setBookingForm((p) => ({ ...p, status: e.target.value }))}>
                <option value="confirmed">Confirmed</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <div className="grid grid-cols-4 gap-2 text-xs">
                {slotGrid.map((slot) => (
                  <button key={slot.time_slot} type="button" onClick={() => slot.status === "free" && setBookingForm((p) => ({ ...p, time_slot: slot.time_slot }))} className={`rounded-lg border px-2 py-2 ${slot.status === "booked" ? "bg-slate-200 text-slate-500" : bookingForm.time_slot === slot.time_slot ? "bg-blue-600 text-white" : "bg-emerald-50 text-emerald-700"}`}>
                    {slot.time_slot}
                  </button>
                ))}
              </div>
              <button className="rounded-lg bg-blue-600 px-3 py-2 text-white">Create booking</button>
            </form>

            <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
              <div className="mb-2 grid grid-cols-3 gap-2 text-sm">
                <Metric label="Confirmed" value={appointmentsData.summary?.confirmed || 0} compact />
                <Metric label="Pending" value={appointmentsData.summary?.pending || 0} compact />
                <Metric label="Cancelled" value={appointmentsData.summary?.cancelled || 0} compact />
              </div>
              <table className="w-full text-sm">
                <thead><tr className="text-left text-slate-500"><th>Patient</th><th>Doctor</th><th>Date/time</th><th>Type</th><th>Status</th><th /></tr></thead>
                <tbody>
                  {(appointmentsData.appointments || []).map((row) => (
                    <tr key={row.id} className="border-t">
                      <td className="py-2">{row.patient_name}</td><td className="py-2">{row.doctor_name}</td><td className="py-2">{row.appointment_date} {row.time_slot}</td>
                      <td className="py-2">{row.appointment_type}</td><td className="py-2">{row.status}</td>
                      <td className="py-2">{row.status !== "cancelled" ? <button className="rounded border px-2 py-1" onClick={async () => { await api.cancelAdminAppointment(row.id); await loadAdminData(); }}>Cancel</button> : null}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TwoCol>

          <TwoCol>
            <form onSubmit={submitProduct} className="rounded-2xl border bg-white p-4 space-y-3">
              <h4 className="font-semibold">{productEditId ? "Edit product" : "Add product"}</h4>
              <input className="w-full rounded-lg border px-3 py-2" placeholder="Product name" value={productForm.name} onChange={(e) => setProductForm((p) => ({ ...p, name: e.target.value }))} />
              <select className="w-full rounded-lg border px-3 py-2" value={productForm.category} onChange={(e) => setProductForm((p) => ({ ...p, category: e.target.value }))}>
                {PRODUCT_CATEGORIES.map((cat) => <option key={cat} value={cat}>{cat}</option>)}
              </select>
              <input className="w-full rounded-lg border px-3 py-2" type="number" placeholder="Price" value={productForm.price} onChange={(e) => setProductForm((p) => ({ ...p, price: e.target.value }))} />
              <input className="w-full rounded-lg border px-3 py-2" type="number" placeholder="Stock quantity" value={productForm.quantity_available} onChange={(e) => setProductForm((p) => ({ ...p, quantity_available: e.target.value }))} />
              <input className="w-full rounded-lg border px-3 py-2" type="number" placeholder="Low stock threshold" value={productForm.stock_threshold} onChange={(e) => setProductForm((p) => ({ ...p, stock_threshold: e.target.value }))} />
              <button className="rounded-lg bg-blue-600 px-3 py-2 text-white">{productEditId ? "Update" : "Add"}</button>
            </form>
            <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 mb-3">
                <Metric label="Total products" value={inventoryData.metrics?.total_products || 0} compact />
                <Metric label="Low stock" value={inventoryData.metrics?.low_stock_count || 0} compact />
                <Metric label="Out of stock" value={inventoryData.metrics?.out_of_stock_count || 0} compact />
                <Metric label="Inventory value" value={inr(inventoryData.metrics?.inventory_value || 0)} compact />
              </div>
              {lowStockAlert ? <p className="mb-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">{lowStockAlert}</p> : null}
              <table className="w-full text-sm">
                <thead><tr className="text-left text-slate-500"><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Status</th><th /></tr></thead>
                <tbody>
                  {(inventoryData.products || []).map((item) => {
                    const max = Math.max(item.stock_threshold * 2, 1);
                    const pct = Math.max(0, Math.min((item.quantity_available / max) * 100, 100));
                    return (
                      <tr key={item.id} className="border-t">
                        <td className="py-2">{item.name}</td><td className="py-2">{item.category}</td><td className="py-2">{inr(item.price)}</td>
                        <td className="py-2"><div className="h-2 w-24 rounded bg-slate-200"><div className="h-2 rounded bg-blue-500" style={{ width: `${pct}%` }} /></div><span className="text-xs">{item.quantity_available}</span></td>
                        <td className="py-2"><span className={`rounded-full px-2 py-1 text-xs ${item.stock_status === "In stock" ? "bg-emerald-100 text-emerald-700" : item.stock_status === "Low stock" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{item.stock_status}</span></td>
                        <td className="py-2 space-x-2">
                          <button className="rounded border px-2 py-1" onClick={() => { setProductEditId(item.id); setProductForm({ name: item.name, category: item.category, price: item.price, quantity_available: item.quantity_available, stock_threshold: item.stock_threshold }); }}>Edit</button>
                          <button className="rounded border border-red-300 px-2 py-1 text-red-700" onClick={async () => { await api.deleteInventoryProduct(item.id); await loadAdminData(); }}>Delete</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </TwoCol>

          <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
            <div className="mb-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Total orders" value={ordersData.metrics?.total_orders || 0} compact />
              <Metric label="Pending" value={ordersData.metrics?.pending || 0} compact />
              <Metric label="Delivered" value={ordersData.metrics?.delivered || 0} compact />
              <Metric label="Total revenue" value={inr(ordersData.metrics?.total_revenue || 0)} compact />
            </div>
            <table className="w-full text-sm">
              <thead><tr className="text-left text-slate-500"><th>Order ID</th><th>Patient</th><th>Items</th><th>Amount</th><th>Date</th><th>Status</th><th /></tr></thead>
              <tbody>
                {(ordersData.orders || []).map((order) => (
                  <tr key={order.id} className="border-t">
                    <td className="py-2">#{order.id}</td><td className="py-2">{order.patient_name}</td><td className="py-2">{(order.items || []).join(", ")}</td>
                    <td className="py-2">{inr(order.total_amount)}</td><td className="py-2">{new Date(order.created_at).toLocaleDateString()}</td><td className="py-2">{order.status}</td>
                    <td className="py-2">{order.status === "pending" ? <button className="rounded border px-2 py-1" onClick={async () => { await api.shipOrder(order.id); await loadAdminData(); }}>Ship</button> : null}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <TwoCol>
          <form onSubmit={submitBooking} className="rounded-2xl border bg-white p-4 space-y-3">
            <h4 className="font-semibold">Book appointment</h4>
            <select className="w-full rounded-lg border px-3 py-2" value={bookingForm.doctor_id} onChange={async (e) => { const doctor_id = e.target.value; setBookingForm((p) => ({ ...p, doctor_id })); await refreshSlots(doctor_id, bookingForm.appointment_date, false); }}>
              <option value="">Select doctor</option>
              {userDoctors.map((doctor) => <option key={doctor.id} value={doctor.id}>{doctor.name} - {doctor.specialization}</option>)}
            </select>
            <input className="w-full rounded-lg border px-3 py-2" type="date" value={bookingForm.appointment_date} onChange={async (e) => { const appointment_date = e.target.value; setBookingForm((p) => ({ ...p, appointment_date })); await refreshSlots(bookingForm.doctor_id, appointment_date, false); }} />
            <select className="w-full rounded-lg border px-3 py-2" value={bookingForm.appointment_type} onChange={(e) => setBookingForm((p) => ({ ...p, appointment_type: e.target.value }))}>
              <option value="in-person">In-person</option>
              <option value="video call">Video</option>
            </select>
            <div className="grid grid-cols-4 gap-2 text-xs">
              {slotGrid.map((slot) => (
                <button key={slot.time_slot} type="button" onClick={() => slot.status === "free" && setBookingForm((p) => ({ ...p, time_slot: slot.time_slot }))} className={`rounded-lg border px-2 py-2 ${slot.status === "booked" ? "bg-slate-200 text-slate-500" : bookingForm.time_slot === slot.time_slot ? "bg-blue-600 text-white" : "bg-emerald-50 text-emerald-700"}`}>
                  {slot.time_slot}
                </button>
              ))}
            </div>
            <button className="rounded-lg bg-blue-600 px-3 py-2 text-white">Place booking request</button>
          </form>

          <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
            <h4 className="font-semibold mb-2">My bookings & orders</h4>
            <table className="w-full text-sm mb-4">
              <thead><tr className="text-left text-slate-500"><th>Doctor</th><th>Date/time</th><th>Type</th><th>Status</th></tr></thead>
              <tbody>
                {userAppointments.map((row) => (
                  <tr key={row.id} className="border-t"><td className="py-2">{row.doctor_name}</td><td className="py-2">{row.appointment_date} {row.time_slot}</td><td className="py-2">{row.appointment_type}</td><td className="py-2">{row.status}</td></tr>
                ))}
              </tbody>
            </table>
            <table className="w-full text-sm">
              <thead><tr className="text-left text-slate-500"><th>Order ID</th><th>Amount</th><th>Date</th><th>Status</th></tr></thead>
              <tbody>
                {userOrders.map((row) => (
                  <tr key={row.id} className="border-t"><td className="py-2">#{row.id}</td><td className="py-2">{inr(row.total_amount)}</td><td className="py-2">{new Date(row.created_at).toLocaleDateString()}</td><td className="py-2">{row.status}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </TwoCol>
      )}
    </section>
  );
}

function Metric({ label, value, compact = false }) {
  return <div className={`rounded-xl border bg-white ${compact ? "p-2" : "p-4"}`}><p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p><p className={`${compact ? "text-lg" : "text-2xl"} font-semibold`}>{value}</p></div>;
}

function TwoCol({ children }) {
  return <div className="grid gap-4 lg:grid-cols-2">{children}</div>;
}
