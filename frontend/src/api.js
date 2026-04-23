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
};
