import { useEffect, useState, useMemo } from "react";
import { api } from "./api";

const PRODUCT_CATEGORIES = ["Monitoring", "Supplements", "Medication", "Diet & Nutrition", "Fitness"];
const inr = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const defaultProduct = { name: "", category: "Monitoring", price: "", quantity_available: "", stock_threshold: 10 };

export default function InventoryManagement({ user }) {
  const [products, setProducts] = useState([]);
  const [riskFilter, setRiskFilter] = useState("all");
  const [metrics, setMetrics] = useState({});
  const [form, setForm] = useState(defaultProduct);
  const [editId, setEditId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const res = await api.adminInventory();
      setProducts(res.products || []);
      setMetrics(res.metrics || {});
    } catch (e) {
      setError(e.message || "Failed to load inventory");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { if (user?.is_admin) load(); }, [user]);

  async function submit(e) {
    e.preventDefault();
    const payload = { ...form, price: Number(form.price || 0), quantity_available: Number(form.quantity_available || 0), stock_threshold: Number(form.stock_threshold || 0) };
    if (editId) await api.updateInventoryProduct(editId, payload);
    else await api.createInventoryProduct(payload);
    setForm(defaultProduct);
    setEditId(null);
    await load();
  }

  const lowStockAlert = useMemo(() => {
    if (metrics.out_of_stock_count > 0) return `${metrics.out_of_stock_count} products are out of stock.`;
    if (metrics.low_stock_count > 0) return `${metrics.low_stock_count} products are below threshold.`;
    return "";
  }, [metrics]);

  if (!user?.is_admin) return null;

  return (
    <section className="glass rounded-3xl p-6 space-y-6">
      <h3 className="text-2xl mb-4">Inventory Management</h3>
      {error && <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <div className="flex gap-4 mb-3">
        <select className="rounded-lg border px-3 py-2" value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
          <option value="all">All</option>
          <option value="high">High Risk</option>
          <option value="moderate">Moderate Risk</option>
        </select>
        <span className="text-xs text-slate-500">Filter by recommended risk level</span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-3">
        <Metric label="Total products" value={metrics.total_products || 0} compact />
        <Metric label="Low stock" value={metrics.low_stock_count || 0} compact />
        <Metric label="Out of stock" value={metrics.out_of_stock_count || 0} compact />
        <Metric label="Inventory value" value={inr(metrics.inventory_value || 0)} compact />
      </div>
      {lowStockAlert && <p className="mb-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">{lowStockAlert}</p>}
      <form onSubmit={submit} className="rounded-2xl border bg-white p-4 space-y-3">
        <h4 className="font-semibold">{editId ? "Edit product" : "Add product"}</h4>
        <input className="w-full rounded-lg border px-3 py-2" placeholder="Product name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
        <select className="w-full rounded-lg border px-3 py-2" value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}>
          {PRODUCT_CATEGORIES.map((cat) => <option key={cat} value={cat}>{cat}</option>)}
        </select>
        <input className="w-full rounded-lg border px-3 py-2" type="number" placeholder="Price" value={form.price} onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))} />
        <input className="w-full rounded-lg border px-3 py-2" type="number" placeholder="Stock quantity" value={form.quantity_available} onChange={(e) => setForm((f) => ({ ...f, quantity_available: e.target.value }))} />
        <input className="w-full rounded-lg border px-3 py-2" type="number" placeholder="Low stock threshold" value={form.stock_threshold} onChange={(e) => setForm((f) => ({ ...f, stock_threshold: e.target.value }))} />
        <button className="rounded-lg bg-blue-600 px-3 py-2 text-white">{editId ? "Update" : "Add"}</button>
      </form>
      <div className="rounded-2xl border bg-white p-4 overflow-x-auto">
        <h4 className="font-semibold mb-2">Product table</h4>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500"><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Status</th><th /></tr></thead>
          <tbody>
            {products
              .filter(item => {
                if (riskFilter === "all") return true;
                if (riskFilter === "high") return (item.recommended_for || "").toLowerCase().includes("high risk") || (item.recommended_for || "").toLowerCase().includes("diabetic");
                if (riskFilter === "moderate") return (item.recommended_for || "").toLowerCase().includes("moderate") || (item.recommended_for || "").toLowerCase().includes("pre-diabetic");
                return true;
              })
              .map((item) => {
              const max = Math.max(item.stock_threshold * 2, 1);
              const pct = Math.max(0, Math.min((item.quantity_available / max) * 100, 100));
              return (
                <tr key={item.id} className="border-t">
                  <td className="py-2">{item.name}</td><td className="py-2">{item.category}</td><td className="py-2">{inr(item.price)}</td>
                  <td className="py-2"><div className="h-2 w-24 rounded bg-slate-200"><div className="h-2 rounded bg-blue-500" style={{ width: `${pct}%` }} /></div><span className="text-xs">{item.quantity_available}</span></td>
                  <td className="py-2"><span className={`rounded-full px-2 py-1 text-xs ${item.stock_status === "In stock" ? "bg-emerald-100 text-emerald-700" : item.stock_status === "Low stock" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{item.stock_status}</span></td>
                  <td className="py-2 space-x-2">
                    <button className="rounded border px-2 py-1" onClick={() => { setEditId(item.id); setForm({ name: item.name, category: item.category, price: item.price, quantity_available: item.quantity_available, stock_threshold: item.stock_threshold }); }}>Edit</button>
                    <button className="rounded border border-red-300 px-2 py-1 text-red-700" onClick={async () => { await api.deleteInventoryProduct(item.id); await load(); }}>Delete</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
function Metric({ label, value, compact }) {
  return <div className="rounded-2xl border bg-white p-4 text-center"><div className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold text-slate-900">{compact ? value : value}</div></div>;
}
