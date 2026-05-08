import { useEffect, useState, useMemo } from "react";
import { api } from "./api";

const inr = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const CATEGORIES = ["All", "Monitoring", "Supplements", "Medication", "Diet & Nutrition", "Fitness", "Services"];

export default function UserStore({ user }) {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [orders, setOrders] = useState([]);
  const [view, setView] = useState("shop"); // "shop" | "cart" | "orders"
  const [category, setCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [cartLoading, setCartLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [address, setAddress] = useState("");
  const [checkingOut, setCheckingOut] = useState(false);
  const [qty, setQty] = useState({});

  async function loadProducts() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (category !== "All") params.append("category", category);
      if (search.trim()) params.append("search", search.trim());
      const res = await api.getProducts(params.toString());
      setProducts(res.products || []);
    } catch (e) {
      setError(e.message || "Failed to load products");
    } finally {
      setLoading(false);
    }
  }

  async function loadCart() {
    try {
      const res = await api.getCart();
      setCart({ items: res.items || [], total: res.total || 0 });
    } catch {
      setCart({ items: [], total: 0 });
    }
  }

  async function loadOrders() {
    try {
      const res = await api.userOrders();
      setOrders(res.orders || []);
    } catch {
      setOrders([]);
    }
  }

  useEffect(() => { loadProducts(); }, [category]);
  useEffect(() => { if (user) { loadCart(); loadOrders(); } }, [user]);

  function flash(msg) {
    setSuccess(msg);
    setTimeout(() => setSuccess(""), 3000);
  }

  async function handleAddToCart(productId) {
    setCartLoading(true);
    setError("");
    try {
      await api.addToCart(productId, qty[productId] || 1);
      await loadCart();
      flash("Added to cart!");
    } catch (e) {
      setError(e.message || "Failed to add to cart");
    } finally {
      setCartLoading(false);
    }
  }

  async function handleRemove(cartItemId) {
    setCartLoading(true);
    try {
      await api.removeFromCart(cartItemId);
      await loadCart();
    } catch (e) {
      setError(e.message || "Failed to remove item");
    } finally {
      setCartLoading(false);
    }
  }

  async function handleCheckout(e) {
    e.preventDefault();
    if (!address.trim()) { setError("Please enter a delivery address."); return; }
    setCheckingOut(true);
    setError("");
    try {
      await api.checkout(address.trim());
      await loadCart();
      await loadOrders();
      setAddress("");
      setView("orders");
      flash("Order placed successfully!");
    } catch (e) {
      setError(e.message || "Checkout failed");
    } finally {
      setCheckingOut(false);
    }
  }

  const filtered = useMemo(() => {
    if (!search.trim()) return products;
    const q = search.toLowerCase();
    return products.filter(p => p.name?.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q));
  }, [products, search]);

  const cartCount = cart.items.reduce((s, i) => s + (i.quantity || 0), 0);

  return (
    <section className="glass rounded-3xl p-6">
      {/* Header */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-2xl font-semibold text-slate-900">Health Store</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setView("shop")}
            className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${view === "shop" ? "bg-blue-600 text-white" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"}`}
          >
            Shop
          </button>
          <button
            onClick={() => { setView("cart"); loadCart(); }}
            className={`relative rounded-xl px-4 py-2 text-sm font-semibold transition ${view === "cart" ? "bg-blue-600 text-white" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"}`}
          >
            Cart
            {cartCount > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                {cartCount}
              </span>
            )}
          </button>
          <button
            onClick={() => { setView("orders"); loadOrders(); }}
            className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${view === "orders" ? "bg-blue-600 text-white" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"}`}
          >
            My Orders
          </button>
        </div>
      </div>

      {error && <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {success && <p className="mb-3 rounded-xl border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{success}</p>}

      {/* ── SHOP VIEW ── */}
      {view === "shop" && (
        <>
          {/* Filters */}
          <div className="mb-4 flex flex-wrap gap-2">
            <input
              type="text"
              placeholder="Search products…"
              value={search}
              onChange={e => { setSearch(e.target.value); }}
              onKeyDown={e => e.key === "Enter" && loadProducts()}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            <button onClick={loadProducts} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-50">Search</button>
          </div>
          <div className="mb-5 flex flex-wrap gap-2">
            {CATEGORIES.map(c => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${category === c ? "bg-blue-600 text-white" : "border border-slate-300 bg-white text-slate-600 hover:bg-slate-50"}`}
              >
                {c}
              </button>
            ))}
          </div>

          {loading ? (
            <p className="text-sm text-slate-500">Loading products…</p>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-slate-500">No products found.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map(product => (
                <div key={product.id} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <span className="mb-1 inline-block w-fit rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">{product.category}</span>
                  <h4 className="font-semibold text-slate-900">{product.name}</h4>
                  {product.description && <p className="mt-1 text-xs text-slate-500 line-clamp-2">{product.description}</p>}
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-base font-bold text-slate-800">{inr(product.price)}</span>
                    <span className={`text-xs font-medium ${product.quantity_available > 0 ? "text-emerald-600" : "text-red-500"}`}>
                      {product.quantity_available > 0 ? `${product.quantity_available} in stock` : "Out of stock"}
                    </span>
                  </div>
                  {product.quantity_available > 0 && (
                    <div className="mt-3 flex items-center gap-2">
                      <select
                        value={qty[product.id] || 1}
                        onChange={e => setQty(q => ({ ...q, [product.id]: Number(e.target.value) }))}
                        className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
                      >
                        {Array.from({ length: Math.min(product.quantity_available, 10) }, (_, i) => i + 1).map(n => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </select>
                      <button
                        disabled={cartLoading}
                        onClick={() => handleAddToCart(product.id)}
                        className="flex-1 rounded-xl bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
                      >
                        Add to Cart
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── CART VIEW ── */}
      {view === "cart" && (
        <>
          {cart.items.length === 0 ? (
            <p className="text-sm text-slate-500">Your cart is empty. <button className="text-blue-600 underline" onClick={() => setView("shop")}>Browse products</button></p>
          ) : (
            <>
              <div className="mb-4 overflow-x-auto rounded-2xl border border-slate-200">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Product</th>
                      <th className="px-4 py-3">Qty</th>
                      <th className="px-4 py-3">Price</th>
                      <th className="px-4 py-3">Subtotal</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {cart.items.map(item => (
                      <tr key={item.id}>
                        <td className="px-4 py-3 font-medium text-slate-800">{item.name}</td>
                        <td className="px-4 py-3 text-slate-600">{item.quantity}</td>
                        <td className="px-4 py-3 text-slate-600">{inr(item.price)}</td>
                        <td className="px-4 py-3 font-semibold text-slate-800">{inr(item.item_total)}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleRemove(item.id)}
                            disabled={cartLoading}
                            className="rounded border border-red-300 px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mb-5 flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <span className="font-semibold text-slate-700">Total</span>
                <span className="text-lg font-bold text-slate-900">{inr(cart.total)}</span>
              </div>

              {/* Checkout form */}
              <form onSubmit={handleCheckout} className="flex flex-col gap-3 rounded-2xl border border-blue-100 bg-blue-50 p-4">
                <h4 className="font-semibold text-slate-800">Checkout</h4>
                <textarea
                  required
                  rows={2}
                  placeholder="Delivery address…"
                  value={address}
                  onChange={e => setAddress(e.target.value)}
                  className="rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
                <button
                  type="submit"
                  disabled={checkingOut}
                  className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60"
                >
                  {checkingOut ? "Placing order…" : `Place Order — ${inr(cart.total)}`}
                </button>
              </form>
            </>
          )}
        </>
      )}

      {/* ── ORDERS VIEW ── */}
      {view === "orders" && (
        <>
          {orders.length === 0 ? (
            <p className="text-sm text-slate-500">No orders yet. <button className="text-blue-600 underline" onClick={() => setView("shop")}>Start shopping</button></p>
          ) : (
            <div className="flex flex-col gap-4">
              {orders.map(order => (
                <div key={order.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <span className="text-xs text-slate-500">Order #{order.id}</span>
                      <span className="ml-3 text-xs text-slate-400">{order.created_at ? new Date(order.created_at).toLocaleDateString() : ""}</span>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                      order.status === "shipped" ? "bg-emerald-100 text-emerald-700" :
                      order.status === "cancelled" ? "bg-red-100 text-red-600" :
                      "bg-amber-100 text-amber-700"
                    }`}>
                      {order.status}
                    </span>
                  </div>
                  {order.items?.length > 0 && (
                    <ul className="mb-2 space-y-1 text-sm text-slate-700">
                      {order.items.map((item, idx) => (
                        <li key={idx} className="flex justify-between">
                          <span>{item.name} × {item.quantity}</span>
                          <span>{inr(item.price * item.quantity)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className="flex justify-end">
                    <span className="font-bold text-slate-900">{inr(order.total_amount)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
