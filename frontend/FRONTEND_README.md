# Frontend — Full Explanation

This document explains every part of the frontend so you can study and present it confidently.

---

## What Is the Frontend?

The frontend is the **user interface** (what users see and interact with in the browser). It:
- Renders all pages and forms
- Collects user input (clinical data, login details, etc.)
- Sends API requests to the backend
- Displays predictions, history, wellness info, and store products
- Manages application state (logged-in user, cart, history, etc.)

---

## Technology Stack

| Technology | What It Does |
|---|---|
| **React** | JavaScript library for building UI as reusable components |
| **Vite** | Fast build tool and dev server (replaces Create React App) |
| **Tailwind CSS** | Utility-first CSS framework — style elements using class names |
| **Framer Motion** | Animation library — smooth transitions and page animations |
| **Recharts** | Chart library built on React — used for trend graphs and bar charts |
| **Lucide React** | Icon library — provides all the SVG icons in the UI |
| **PostCSS + Autoprefixer** | Processes CSS and adds browser compatibility prefixes |

---

## Folder Structure

```
frontend/
├── index.html              # The single HTML file — React mounts inside #root
├── vite.config.js          # Vite config — dev server, proxy settings
├── tailwind.config.cjs     # Tailwind config — custom colours, fonts
├── postcss.config.cjs      # PostCSS plugins config
├── package.json            # All dependencies and npm scripts
├── Dockerfile              # Instructions to build and serve with Nginx
├── nginx.conf              # Nginx config — proxies /api to backend
└── src/
    ├── main.jsx            # Entry point — mounts App into the DOM
    ├── App.jsx             # Root component — all pages and state live here
    ├── api.js              # All backend API calls in one place
    ├── index.css           # Global CSS and Tailwind imports
    ├── HealthcareManagement.jsx  # Admin + user healthcare management panel
    ├── UserStore.jsx             # Product shop, cart, and orders for users
    ├── AppointmentBooking.jsx    # Doctor appointment booking interface
    ├── InventoryManagement.jsx   # Admin inventory management
    └── OrderManagement.jsx       # Admin order management
```

---

## How React Works

React builds the UI as a tree of **components** — small, reusable functions that return HTML-like code (called JSX).

```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}
```

React only updates the parts of the page that change — this makes it very fast.

### JSX

JSX is a syntax that looks like HTML but is actually JavaScript:

```jsx
const element = <button className="btn" onClick={() => alert('clicked')}>Click me</button>;
```

- Use `className` instead of `class` (since `class` is a reserved JS keyword)
- JavaScript expressions go inside `{ }`

---

## Entry Point (`main.jsx`)

This is where React starts:

```jsx
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- Finds the `<div id="root">` in `index.html`
- Renders the entire `<App />` component inside it
- `React.StrictMode` helps catch bugs during development

---

## Root Component (`App.jsx`)

`App.jsx` is the **main hub** of the entire application. It contains:

### State Management with `useState`

```jsx
const [user, setUser] = useState(null);        // logged-in user or null
const [activeTab, setActiveTab] = useState("predict");
const [history, setHistory] = useState([]);
const [payload, setPayload] = useState(defaultPayload);
```

`useState` is a React **hook** — it stores values that, when changed, cause the component to re-render.

### Side Effects with `useEffect`

```jsx
useEffect(() => {
  api.checkSession().then(setUser).catch(() => setUser(null));
}, []);
```

`useEffect` runs code after render. Here it checks if a user is already logged in when the page loads (empty `[]` dependency means it runs once on mount).

### Input Form Fields

The 9 clinical input fields are defined as a data array:

```jsx
const fields = [
  { key: "glucose", label: "Glucose", min: 0, max: 300, step: 1, tip: "..." },
  { key: "bmi",     label: "BMI",     min: 10, max: 60, step: 0.1 },
  // ...
];
```

This array drives the form — one input rendered per field using `.map()`.

### Guest Mode

Users can use the prediction form without logging in. Guest results are saved to `localStorage` under the key `guest_prediction_history_v1`:

```jsx
const GUEST_HISTORY_KEY = "guest_prediction_history_v1";

function loadGuestHistoryFromStorage() {
  const raw = window.localStorage.getItem(GUEST_HISTORY_KEY);
  return raw ? JSON.parse(raw) : [];
}
```

---

## API Layer (`api.js`)

All HTTP calls to the backend are centralised in `api.js`. This avoids repeating `fetch()` logic everywhere.

### Base URL

```js
const API_BASE = import.meta.env.VITE_API_BASE || "/api";
```

- In development, Vite's proxy forwards `/api` requests to `http://localhost:5000`
- In production (Docker/Nginx), `/api` is proxied by Nginx to the backend container

### The `request` Helper

```js
async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",       // send session cookies with every request
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.status === "error") {
    throw new Error(data.message || "Request failed");
  }
  return data;
}
```

- `credentials: "include"` — required so the browser sends the session cookie to the backend
- Throws an error if the response is not OK, so calling code can use `try/catch`

### API Methods

```js
export const api = {
  checkSession: () => request("/auth/check"),
  login:        (payload) => request("/auth/login",    { method: "POST", body: JSON.stringify(payload) }),
  register:     (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  logout:       () => request("/auth/logout", { method: "POST" }),
  predict:      (payload) => request("/predict",       { method: "POST", body: JSON.stringify(payload) }),
  getProducts:  (params)  => request(`/store/products?${params}`),
  addToCart:    (id, qty) => request("/store/cart/add", { method: "POST", body: JSON.stringify({ product_id: id, quantity: qty }) }),
  checkout:     (address) => request("/store/checkout", { method: "POST", body: JSON.stringify({ shipping_address: address }) }),
  // ...and many more
};
```

---

## Vite Dev Server (`vite.config.js`)

```js
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
});
```

### What the Proxy Does

Without a proxy, calling `/api/predict` from the browser would go to `localhost:5173/api/predict` (Vite's server) — not the Flask backend.

The proxy **forwards** any request starting with `/api` to `http://localhost:5000` automatically during development. This avoids CORS issues in local dev.

---

## Tailwind CSS

Tailwind is a **utility-first** CSS framework. Instead of writing custom CSS, you apply pre-built class names directly to HTML elements:

```jsx
<button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
  Predict
</button>
```

Each class name does exactly one thing:
- `bg-blue-600` → background color blue
- `text-white` → white text
- `px-4` → horizontal padding
- `rounded-lg` → rounded corners
- `hover:bg-blue-700` → darker blue on hover

---

## Framer Motion (Animations)

Framer Motion adds smooth animations to React components:

```jsx
import { motion, AnimatePresence } from "framer-motion";

<motion.div
  initial={{ opacity: 0, y: 20 }}    // starts invisible, shifted down
  animate={{ opacity: 1, y: 0 }}     // animates to visible, normal position
  exit={{ opacity: 0 }}              // fades out when removed
  transition={{ duration: 0.3 }}
>
  Result Card
</motion.div>
```

- `initial` — state before animation starts
- `animate` — target state
- `exit` — state when component is removed from DOM
- `AnimatePresence` — needed to enable exit animations

---

## Recharts (Charts)

Recharts renders data visualizations as React components:

```jsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

<ResponsiveContainer width="100%" height={200}>
  <LineChart data={assessmentTrend}>
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="count" stroke="#3b82f6" />
  </LineChart>
</ResponsiveContainer>
```

Used in the Admin Dashboard to show:
- 14-day assessment trend (LineChart)
- Diabetic vs non-diabetic count (BarChart)

---

## Lucide React (Icons)

Lucide provides SVG icons as React components:

```jsx
import { HeartPulse, Brain, LogOut, Stethoscope } from "lucide-react";

<HeartPulse className="w-5 h-5 text-red-500" />
```

Icons used in this project: `Bot`, `Brain`, `Database`, `HeartPulse`, `LogOut`, `Mic`, `MicOff`, `ShieldCheck`, `Sparkles`, `Stethoscope`, `TrendingUp`

---

## Component Breakdown

### `App.jsx` — Root / Main Page

Handles:
- Login / Register forms
- Prediction form (8 clinical inputs)
- Prediction result display (risk band, confidence, explanations)
- Prediction history (logged-in users from DB; guests from localStorage)
- Admin dashboard (charts, user stats)
- Navigation tabs: Predict, History, Wellness, Store, Healthcare

### `HealthcareManagement.jsx` — Healthcare Admin Panel

**Admin view:**
- Manage doctors (add, edit, delete)
- View and manage appointments
- View inventory and orders

**User view:**
- Browse available doctors
- Book appointments by selecting date and time slot
- View own appointments

Role is determined by `user.is_admin`:
```jsx
const isAdmin = Boolean(user?.is_admin);
```

### `UserStore.jsx` — Product Shop

- Browse health products with category filter and search
- Add items to cart with quantity selector
- View and manage cart
- Checkout with shipping address
- View past orders
- Prices displayed in Indian Rupees (₹) using `toLocaleString("en-IN")`

### `AppointmentBooking.jsx` — Appointment Booking

- Loads doctors list
- Selects doctor → date → available time slots
- Submits booking (works for both admin and regular users)
- Shows existing appointments

### `InventoryManagement.jsx` — Admin Inventory

- View all products with stock metrics (total, out-of-stock, low-stock)
- Add new products
- Edit product details and stock levels
- Delete products

### `OrderManagement.jsx` — Admin Orders

- View all orders with status
- Ship/update order status

---

## How Data Flows

```
User fills form in App.jsx
        ↓
React updates state with useState
        ↓
User clicks Submit → api.predict(payload) called
        ↓
fetch() sends POST /api/predict to backend
        ↓
Backend returns { prediction, confidence, risk_band, explanations }
        ↓
React updates state with result
        ↓
Component re-renders showing the result card
```

---

## Building for Production

```powershell
cd frontend
npm run build
```

Vite compiles everything into `dist/` — optimized HTML, CSS, and JS bundles.

The `frontend/Dockerfile` then:
1. Runs `npm run build`
2. Serves the `dist/` folder with **Nginx**
3. Nginx proxies `/api` requests to the Flask backend container

---

## Running Locally (Development)

```powershell
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

> The Vite proxy automatically forwards all `/api` calls to the backend at `http://localhost:5000`

---

## Environment Variable

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE` | `/api` | Base URL for all API calls |

Set in a `.env` file:
```
VITE_API_BASE=/api
```

In production behind Nginx, `/api` is proxied to the backend. In a different deployment, you could set this to `https://your-backend.com/api`.

---

## Summary — What Each File Does

| File | Role |
|---|---|
| `main.jsx` | Entry point, mounts React app |
| `App.jsx` | All main UI: predict form, results, history, dashboard, navigation |
| `api.js` | Every backend API call in one place |
| `HealthcareManagement.jsx` | Doctors, appointments, admin + user view |
| `UserStore.jsx` | Shop, cart, checkout, orders |
| `AppointmentBooking.jsx` | Book doctor appointments |
| `InventoryManagement.jsx` | Admin: manage product stock |
| `OrderManagement.jsx` | Admin: manage and ship orders |
| `index.css` | Global styles + Tailwind base imports |
| `vite.config.js` | Dev server config, API proxy |
| `tailwind.config.cjs` | Tailwind customization |
