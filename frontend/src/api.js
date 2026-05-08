const API_BASE = import.meta.env.VITE_API_BASE || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.status === "error") {
    throw new Error(data.message || "Request failed");
  }
  return data;
}

export const api = {
  checkSession: () => request("/auth/check"),
  login: (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  register: (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  predict: (payload) => request("/predict", { method: "POST", body: JSON.stringify(payload) }),
  saveAssessment: (payload) => request("/wellness/risk-assessment", { method: "POST", body: JSON.stringify(payload) }),
  getHistory: () => request("/wellness/risk-assessment/history"),
  getAdminOverview: () => request("/wellness/admin/overview"),
  chatbot: (payload) => request("/wellness/chatbot", { method: "POST", body: JSON.stringify(payload) }),
  adminDashboard: () => request("/admin/dashboard"),
  adminDoctors: () => request("/admin/doctors"),
  createDoctor: (payload) => request("/admin/doctors", { method: "POST", body: JSON.stringify(payload) }),
  updateDoctor: (doctorId, payload) => request(`/admin/doctors/${doctorId}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteDoctor: (doctorId) => request(`/admin/doctors/${doctorId}`, { method: "DELETE" }),
  adminAppointmentSlots: (doctorId, date) => request(`/admin/appointments/slots?doctor_id=${doctorId}&date=${date}`),
  adminAppointments: (date) => request(`/admin/appointments${date ? `?date=${date}` : ""}`),
  createAdminAppointment: (payload) => request("/admin/appointments", { method: "POST", body: JSON.stringify(payload) }),
  cancelAdminAppointment: (appointmentId) => request(`/admin/appointments/${appointmentId}/cancel`, { method: "PATCH" }),
  adminInventory: () => request("/store/products"),
  createInventoryProduct: (payload) => request("/store/products", { method: "POST", body: JSON.stringify(payload) }),
  updateInventoryProduct: (productId, payload) => request(`/store/products/${productId}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteInventoryProduct: (productId) => request(`/store/products/${productId}`, { method: "DELETE" }),
  adminOrders: () => request("/store/orders"),
  shipOrder: (orderId) => request(`/store/orders/${orderId}/ship`, { method: "PATCH" }),
  userDoctors: () => request("/user/doctors"),
  userAppointmentSlots: (doctorId, date) => request(`/user/appointments/slots?doctor_id=${doctorId}&date=${date}`),
  createUserAppointment: (payload) => request("/user/appointments", { method: "POST", body: JSON.stringify(payload) }),
  userAppointments: () => request("/user/appointments"),
  userOrders: () => request("/store/orders"),
  // Shop / Cart
  getProducts: (params) => request(`/store/products${params ? `?${params}` : ""}`),
  getCart: () => request("/store/cart"),
  addToCart: (productId, quantity = 1) => request("/store/cart/add", { method: "POST", body: JSON.stringify({ product_id: productId, quantity }) }),
  removeFromCart: (cartItemId) => request(`/store/cart/remove/${cartItemId}`, { method: "DELETE" }),
  clearCart: () => request("/store/cart/clear", { method: "POST" }),
  checkout: (shippingAddress) => request("/store/checkout", { method: "POST", body: JSON.stringify({ shipping_address: shippingAddress }) }),
};
