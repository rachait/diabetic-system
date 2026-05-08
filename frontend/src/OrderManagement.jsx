import { useEffect, useState } from "react";
import { api } from "./api";

const inr = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

export default function OrderManagement({ user }) {
  const [orders, setOrders] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const res = user?.is_admin ? await api.adminOrders() : await api.userOrders();
      setOrders(res.orders || []);
      setMetrics(res.metrics || {});
    } catch (e) {
      setError(e.message || "Failed to load orders");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [user]);

  async function shipOrder(orderId) {
    await api.shipOrder(orderId);
    await load();
  }

  if (!user) return null;

  return (
    <section className="glass rounded-3xl p-6 space-y-6">
      <h3 className="text-2xl mb-4">Order Management</h3>
      {error && <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-3">
        <Metric label="Total orders" value={metrics.total_orders || 0} compact />
        <Metric label="Pending" value={metrics.pending || 0} compact />
        <Metric label="Delivered" value={metrics.delivered || 0} compact />
        <Metric label="Total revenue" value={inr(metrics.total_revenue || 0)} compact />
      </div>
      <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
        <h4 className="font-semibold mb-2">Order table</h4>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500"><th>Order ID</th><th>Patient</th><th>Items</th><th>Amount</th><th>Date</th><th>Status</th><th /></tr></thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id} className="border-t">
                <td className="py-2">{order.id}</td>
                <td className="py-2">{order.patient_name}</td>
                <td className="py-2">{order.items?.map((item) => `${item.name} x${item.quantity}`).join(", ")}</td>
                <td className="py-2">{inr(order.total_amount)}</td>
                <td className="py-2">{order.created_at?.slice(0, 10)}</td>
                <td className="py-2"><span className={`rounded-full px-2 py-1 text-xs ${order.status === "pending" ? "bg-amber-100 text-amber-700" : order.status === "delivered" ? "bg-emerald-100 text-emerald-700" : "bg-blue-100 text-blue-700"}`}>{order.status}</span></td>
                <td className="py-2">
                  {user.is_admin && order.status === "pending" ? (
                    <button className="rounded border px-2 py-1" onClick={() => shipOrder(order.id)}>Ship</button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
function Metric({ label, value, compact }) {
  return <div className="rounded-2xl border bg-white p-4 text-center"><div className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold text-slate-900">{compact ? value : value}</div></div>;
}
