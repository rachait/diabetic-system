import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bot,
  Brain,
  Database,
  HeartPulse,
  LogOut,
  Mic,
  MicOff,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api";
import HealthcareManagement from "./HealthcareManagement";
import UserStore from "./UserStore";

const fields = [
  { key: "pregnancies", label: "Pregnancies", min: 0, max: 20, step: 1, tip: "Total number of pregnancies." },
  {
    key: "gender",
    label: "Gender",
    type: "select",
    tip: "Select the user's gender for record-keeping and future model support.",
    options: ["Male", "Female", "Other"],
  },
  { key: "glucose", label: "Glucose", min: 0, max: 300, step: 1, tip: "Plasma glucose concentration in mg/dL. Enter a value between 0 and 300." },
  { key: "blood_pressure", label: "Blood Pressure", min: 0, max: 200, step: 1, tip: "Diastolic blood pressure (mm Hg)." },
  { key: "skin_thickness", label: "Skin Thickness", min: 0, max: 100, step: 1, tip: "Triceps skin fold thickness (mm)." },
  { key: "insulin", label: "Insulin", min: 0, max: 900, step: 1, tip: "2-Hour serum insulin (mu U/ml)." },
  { key: "bmi", label: "BMI", min: 10, max: 60, step: 0.1, tip: "Body Mass Index." },
  { key: "age", label: "Age", min: 1, max: 120, step: 1, tip: "Age in years." },
  {
    key: "diabetes_pedigree",
    label: "Diabetes Pedigree",
    min: 0,
    max: 3,
    step: 0.01,
    tip: "Family diabetes likelihood factor.",
  },
];

const defaultPayload = {
  pregnancies: "",
  gender: "Male",
  glucose: "",
  blood_pressure: "",
  skin_thickness: "",
  insulin: "",
  bmi: "",
  age: "",
  diabetes_pedigree: "0.47",
};

const GUEST_HISTORY_KEY = "guest_prediction_history_v1";

function loadGuestHistoryFromStorage() {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(GUEST_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function normalizeGenderValue(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (["male", "man", "boy"].includes(normalized)) return "Male";
  if (["female", "woman", "girl"].includes(normalized)) return "Female";
  if (["other", "non-binary", "nonbinary"].includes(normalized)) return "Other";
  return "";
}

function saveGuestHistoryToStorage(entries) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(GUEST_HISTORY_KEY, JSON.stringify(entries.slice(0, 50)));
}

const cardReveal = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: "easeOut" },
};

const introHighlights = [
  { icon: ShieldCheck, label: "Privacy-first screening" },
  { icon: Brain, label: "ML-guided risk analysis" },
  { icon: Sparkles, label: "Motion-led clinical UI" },
];

const introSignals = [
  { label: "Glucose", value: "132", tone: "text-cyan-700" },
  { label: "Trend", value: "Stable", tone: "text-emerald-700" },
  { label: "Focus", value: "3D", tone: "text-blue-700" },
];

function IntroExperience({ onEnter }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="fixed inset-0 z-50 overflow-hidden bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.28),transparent_34%),radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.22),transparent_28%),linear-gradient(135deg,rgba(3,7,18,0.94),rgba(15,23,42,0.88))] px-4 py-5 text-white backdrop-blur-2xl sm:px-6"
    >
      <div className="pointer-events-none absolute inset-0 intro-grid opacity-50" />
      <motion.div
        aria-hidden="true"
        className="absolute -left-20 top-10 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl"
        animate={{ x: [0, 24, 0], y: [0, -18, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden="true"
        className="absolute bottom-4 right-0 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl"
        animate={{ x: [0, -18, 0], y: [0, 16, 0] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="mx-auto grid h-full max-w-7xl items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="relative z-10 max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.35em] text-cyan-100 shadow-lg shadow-cyan-950/30">
            <Sparkles size={14} /> Immersive 3D intro
          </div>
          <h2 className="mt-5 text-5xl font-semibold leading-none tracking-tight text-white sm:text-6xl lg:text-7xl">
            Diabetes prediction as a cinematic health cockpit.
          </h2>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-200 sm:text-lg">
            Explore a motion-first interface where the model, the charting, and the wellness guidance all feel like
            part of one living clinical system.
          </p>

          <div className="mt-7 flex flex-wrap gap-3">
            {introHighlights.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-slate-100 shadow-lg shadow-slate-950/20 backdrop-blur-xl"
                >
                  <span className="grid h-9 w-9 place-content-center rounded-xl bg-white/10 text-cyan-200">
                    <Icon size={16} />
                  </span>
                  {item.label}
                </div>
              );
            })}
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={onEnter}
              className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_14px_40px_rgba(255,255,255,0.18)] transition hover:-translate-y-0.5"
            >
              Enter dashboard
            </button>
            <p className="text-sm text-slate-300">Cinematic intro, animated layers, and 3D depth by design.</p>
          </div>
        </motion.div>

        <motion.div
          aria-hidden="true"
          initial={{ opacity: 0, scale: 0.92, rotateX: 8 }}
          animate={{ opacity: 1, scale: 1, rotateX: 0 }}
          transition={{ duration: 0.9, ease: "easeOut" }}
          className="relative mx-auto h-[30rem] w-full max-w-[34rem]"
          style={{ perspective: 1600 }}
        >
          <motion.div
            animate={{ rotateX: [10, 4, 10], rotateY: [-16, 12, -16], y: [0, -10, 0] }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
            className="relative h-full w-full rounded-[2rem] border border-white/25 bg-white/10 p-5 shadow-2xl shadow-blue-950/30 backdrop-blur-2xl"
            style={{ transformStyle: "preserve-3d" }}
          >
            <div className="absolute inset-0 rounded-[2rem] bg-[linear-gradient(145deg,rgba(255,255,255,0.16),rgba(255,255,255,0.03))]" />
            <div className="absolute inset-8 rounded-[1.5rem] border border-cyan-100/20" />

            <motion.div
              className="absolute left-6 top-6 rounded-2xl border border-white/20 bg-slate-950/45 px-4 py-3 text-xs text-slate-100 shadow-lg shadow-slate-950/30 backdrop-blur-xl"
              animate={{ y: [0, -10, 0], x: [0, 6, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              style={{ transform: "translateZ(70px)" }}
            >
              <p className="uppercase tracking-[0.3em] text-cyan-200">Live signal</p>
              <p className="mt-1 text-sm font-semibold text-white">Adaptive prediction mesh</p>
            </motion.div>

            <motion.div
              className="absolute right-6 top-14 rounded-2xl border border-white/20 bg-white/10 px-4 py-3 text-xs text-slate-100 shadow-lg shadow-slate-950/30 backdrop-blur-xl"
              animate={{ y: [0, 8, 0], x: [0, -6, 0] }}
              transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
              style={{ transform: "translateZ(50px)" }}
            >
              <p className="uppercase tracking-[0.3em] text-emerald-200">Risk band</p>
              <p className="mt-1 text-sm font-semibold text-white">Clinically guided motion</p>
            </motion.div>

            <div className="relative flex h-full items-center justify-center">
              <motion.div
                className="absolute h-72 w-72 rounded-full border border-cyan-200/35"
                animate={{ rotate: 360 }}
                transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
              />
              <motion.div
                className="absolute h-56 w-56 rounded-full border border-white/30"
                animate={{ rotate: -360 }}
                transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
              />
              <motion.div
                className="absolute h-40 w-40 rounded-full border border-blue-200/45"
                animate={{ rotate: 360 }}
                transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
              />

              <motion.div
                className="absolute h-56 w-56 rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.98),rgba(115,194,255,0.7)_32%,rgba(59,130,246,0.65)_58%,rgba(15,23,42,0.95)_100%)] shadow-[0_0_120px_rgba(56,189,248,0.42)]"
                animate={{ scale: [1, 1.05, 1], rotate: [0, 8, 0] }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                style={{ transform: "translateZ(110px)" }}
              />

              <motion.div
                className="absolute h-20 w-20 rounded-full border border-white/60 bg-white/30 backdrop-blur-md"
                animate={{ y: [0, -16, 0], x: [0, 14, 0] }}
                transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
                style={{ transform: "translate(-140px, -120px) translateZ(90px)" }}
              />
              <motion.div
                className="absolute h-14 w-14 rounded-2xl border border-cyan-100/50 bg-cyan-200/40 backdrop-blur-md"
                animate={{ y: [0, 18, 0], x: [0, -10, 0] }}
                transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut" }}
                style={{ transform: "translate(150px, 100px) translateZ(100px)" }}
              />

              <motion.div
                className="absolute bottom-6 left-6 right-6 rounded-[1.5rem] border border-white/20 bg-slate-950/40 p-4 shadow-xl shadow-slate-950/30 backdrop-blur-xl"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                style={{ transform: "translateZ(120px)" }}
              >
                <div className="flex items-end gap-2">
                  {[34, 58, 44, 72, 55, 80, 67].map((height, index) => (
                    <motion.span
                      key={height}
                      className="w-full rounded-full bg-gradient-to-t from-cyan-400 to-blue-200"
                      animate={{ scaleY: [0.75, 1, 0.8] }}
                      transition={{ duration: 2.8, repeat: Infinity, delay: index * 0.12 }}
                      style={{ height: `${height}px`, transformOrigin: "bottom" }}
                    />
                  ))}
                </div>
                <div className="mt-3 flex items-center justify-between text-xs uppercase tracking-[0.28em] text-slate-300">
                  <span>Motion pattern</span>
                  <span>Confidence stream</span>
                </div>
              </motion.div>

              <div className="absolute left-1/2 top-1/2 h-[22rem] w-[22rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/15 blur-3xl" />
            </div>
          </motion.div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {introSignals.map((signal, index) => (
              <motion.div
                key={signal.label}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.15 * index }}
                className="rounded-2xl border border-white/15 bg-white/10 p-4 text-white shadow-lg shadow-slate-950/20 backdrop-blur-xl"
              >
                <p className="text-xs uppercase tracking-[0.3em] text-slate-300">{signal.label}</p>
                <p className={`mt-2 text-2xl font-semibold ${signal.tone}`}>{signal.value}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

function App() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(defaultPayload);
  const [errors, setErrors] = useState({});
  const [result, setResult] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ username: "", email: "", password: "", full_name: "" });
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState(() => loadGuestHistoryFromStorage());
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [listeningTarget, setListeningTarget] = useState(null);
  const [showIntro, setShowIntro] = useState(true);
  const [adminOverview, setAdminOverview] = useState(null);
  const [loadingAdminOverview, setLoadingAdminOverview] = useState(false);
  const [adminOverviewError, setAdminOverviewError] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content: "I’m your AI wellness assistant. Ask me anything about your result, food, exercise, prevention, or follow-up care.",
    },
  ]);

  const progress = Math.round(((step + 1) / fields.length) * 100);
  const currentField = fields[step];
  const recognitionRef = useRef(null);

  const speechSupported =
    typeof window !== "undefined" &&
    ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

  useEffect(() => {
    const init = async () => {
      try {
        const session = await api.checkSession();
        if (session.authenticated) {
          setUser(session.user);
          await loadHistory();
          if (session.user?.is_admin) {
            await loadAdminOverview();
          }
        } else {
          setHistory(loadGuestHistoryFromStorage());
        }
      } catch {
        setHistory(loadGuestHistoryFromStorage());
      }
    };
    init();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const prefersReducedMotion =
      typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timeout = window.setTimeout(() => setShowIntro(false), prefersReducedMotion ? 900 : 5200);
    return () => window.clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (!speechSupported) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onend = () => setListeningTarget(null);
    recognition.onerror = () => setListeningTarget(null);
    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [speechSupported]);

  async function loadHistory() {
    try {
      const data = await api.getHistory();
      setHistory(data.assessments || []);
    } catch {
      setHistory([]);
    }
  }

  async function loadAdminOverview() {
    setLoadingAdminOverview(true);
    setAdminOverviewError("");
    try {
      const data = await api.getAdminOverview();
      setAdminOverview(data);
    } catch (error) {
      setAdminOverview(null);
      setAdminOverviewError(error.message || "Could not load admin overview.");
    } finally {
      setLoadingAdminOverview(false);
    }
  }

  function validateField(field, value) {
    if (value === "") return "This field is required.";
    if (field.type === "select") {
      if (!field.options.includes(value)) return "Choose a valid option.";
      return "";
    }
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return "Enter a valid number.";
    if (numeric < field.min || numeric > field.max) {
      return `Value must be between ${field.min} and ${field.max}.`;
    }
    return "";
  }

  function handleStepNext() {
    const message = validateField(currentField, form[currentField.key]);
    if (message) {
      setErrors((prev) => ({ ...prev, [currentField.key]: message }));
      return;
    }
    setErrors((prev) => ({ ...prev, [currentField.key]: "" }));
    if (step < fields.length - 1) setStep((s) => s + 1);
  }

  function payloadFromForm() {
    return Object.fromEntries(
      Object.entries(form).map(([key, value]) => {
        const field = fields.find((item) => item.key === key);
        return [key, field?.type === "select" ? value : Number(value)];
      })
    );
  }

  async function runPrediction(event) {
    event.preventDefault();

    const fieldErrors = {};
    for (const field of fields) {
      const message = validateField(field, form[field.key]);
      if (message) fieldErrors[field.key] = message;
    }
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0) return;

    setLoadingPrediction(true);
    try {
      const payload = payloadFromForm();
      const prediction = await api.predict(payload);
      setResult(prediction);

      if (user) {
        try {
          await api.saveAssessment(payload);
          await loadHistory();
        } catch {
          // Keep UX smooth even if history save fails.
        }
      } else {
        const guestRow = {
          id: `guest-${Date.now()}`,
          created_at: new Date().toISOString(),
          confidence: prediction?.confidence ?? null,
          prediction: prediction?.prediction || "Unknown",
          risk_level: prediction?.risk_level || "medium",
        };
        const merged = [guestRow, ...loadGuestHistoryFromStorage()].slice(0, 50);
        saveGuestHistoryToStorage(merged);
        setHistory(merged);
      }
    } catch (error) {
      setResult({
        prediction: "Unavailable",
        risk_level: "medium",
        confidence: null,
        suggestions: [error.message || "Could not generate prediction."],
      });
    } finally {
      setLoadingPrediction(false);
    }
  }

  async function submitAuth(event) {
    event.preventDefault();
    try {
      let authenticatedUser = null;
      if (authMode === "login") {
        const data = await api.login({ username: authForm.username, password: authForm.password });
        authenticatedUser = {
          username: data.username,
          email: data.email,
          full_name: data.full_name,
          is_admin: data.is_admin,
        };
        setUser(authenticatedUser);
      } else {
        await api.register(authForm);
        const session = await api.checkSession();
        authenticatedUser = session.user || null;
        setUser(authenticatedUser);
      }
      setAuthForm({ username: "", email: "", password: "", full_name: "" });
      await loadHistory();
      const isAdmin = Boolean(authenticatedUser?.is_admin);
      if (isAdmin) {
        await loadAdminOverview();
      } else {
        setAdminOverview(null);
      }
    } catch (error) {
      alert(error.message);
    }
  }

  async function handleLogout() {
    await api.logout().catch(() => null);
    setUser(null);
    setHistory(loadGuestHistoryFromStorage());
    setAdminOverview(null);
    setAdminOverviewError("");
  }

  async function submitAssistantQuestion(questionText) {
    const prompt = questionText.trim();
    if (!prompt) return;

    const nextMessages = [...chatMessages, { role: "user", content: prompt }];
    setChatMessages(nextMessages);
    setChatQuestion("");
    setChatLoading(true);

    try {
      const data = await api.chatbot({
        question: prompt,
        risk_level: result?.risk_level || "",
        glucose: form.glucose,
        bmi: form.bmi,
        messages: nextMessages.slice(-8),
      });
      const insightsText = data.insights?.length ? ` Insights: ${data.insights.join(" ")}` : "";
      setChatMessages((prev) => [...prev, { role: "assistant", content: `${data.answer}${insightsText}` }]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "I could not answer right now. Please try again in a moment." },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  async function askAssistant() {
    await submitAssistantQuestion(chatQuestion);
  }

  function toggleVoiceInput(target) {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    if (listeningTarget === target) {
      recognition.stop();
      setListeningTarget(null);
      return;
    }

    if (listeningTarget && listeningTarget !== target) {
      recognition.stop();
    }

    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript?.trim() || "";
      if (!transcript) return;

      if (target === "field") {
        const spokenValue = currentField.type === "select"
          ? normalizeGenderValue(transcript)
          : ((transcript.match(/-?\d+(\.\d+)?/) || [""])[0]);
        setForm((prev) => ({ ...prev, [currentField.key]: spokenValue }));
        setErrors((prev) => ({
          ...prev,
          [currentField.key]: validateField(currentField, spokenValue),
        }));
      }

      if (target === "chat") {
        setChatQuestion(transcript);
        void submitAssistantQuestion(transcript);
      }
    };

    setListeningTarget(target);
    recognition.start();
  }

  const chartData = useMemo(
    () =>
      history
        .slice(0, 12)
        .reverse()
        .map((item) => ({
          date: new Date(item.created_at).toLocaleDateString(),
          confidence: Number(item.confidence || 0) * 100,
        })),
    [history]
  );

  const adminTrendData = useMemo(
    () =>
      (adminOverview?.trends || []).map((row) => ({
        day: row.day,
        total: Number(row.total || 0),
        diabetic: Number(row.diabetic || 0),
      })),
    [adminOverview]
  );

  const trendSummary = useMemo(() => {
    if (history.length < 2) {
      return {
        label: "Baseline",
        detail: "Add at least two predictions to calculate trajectory.",
      };
    }

    const riskWeight = { high: 3, medium: 2, low: 1 };
    const latest = history[0];
    const previous = history[1];
    const latestRisk = riskWeight[(latest?.risk_level || "medium").toLowerCase()] || 2;
    const previousRisk = riskWeight[(previous?.risk_level || "medium").toLowerCase()] || 2;
    const delta = latestRisk - previousRisk;

    if (delta < 0) {
      return {
        label: "Improving",
        detail: "Latest risk band is lower than your previous assessment.",
      };
    }
    if (delta > 0) {
      return {
        label: "Needs Attention",
        detail: "Latest risk band increased. Follow the action plan closely.",
      };
    }
    return {
      label: "Stable",
      detail: "Latest risk band is unchanged from your previous assessment.",
    };
  }, [history]);

  const confidencePercent =
    result?.confidence !== null && result?.confidence !== undefined
      ? Math.round(result.confidence * 100)
      : 0;
  const riskColor =
    result?.risk_level === "high"
      ? "text-red-500"
      : result?.risk_level === "medium"
      ? "text-amber-500"
      : "text-emerald-500";

  return (
    <div className="relative min-h-screen overflow-hidden pb-14">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-20 top-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute right-[-6rem] top-40 h-96 w-96 rounded-full bg-blue-500/15 blur-3xl" />
        <div className="absolute bottom-10 left-1/3 h-64 w-64 rounded-full bg-emerald-300/15 blur-3xl" />
      </div>

      <AnimatePresence>
        {showIntro ? <IntroExperience onEnter={() => setShowIntro(false)} /> : null}
      </AnimatePresence>

      <header className="sticky top-0 z-40 border-b border-white/50 bg-white/70 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ y: [0, -2, 0], rotate: [0, 6, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="rounded-2xl bg-gradient-to-br from-blue-600 via-cyan-500 to-emerald-400 p-2.5 text-white shadow-lg shadow-blue-500/25"
            >
              <HeartPulse size={18} />
            </motion.div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-500">AI Medical Assistant</p>
              <h1 className="text-lg font-bold text-slate-900">Diabetes Prediction Dashboard</h1>
            </div>
          </div>
          {user ? (
            <button onClick={handleLogout} className="flex items-center gap-2 rounded-full border border-slate-300 bg-white/80 px-4 py-2 text-sm shadow-sm transition hover:-translate-y-0.5">
              <LogOut size={14} /> Logout
            </button>
          ) : null}
        </div>
      </header>

      <main className="mx-auto mt-6 max-w-7xl space-y-7 px-4 sm:px-6">
        <motion.section {...cardReveal} className="glass relative overflow-hidden rounded-[2rem] p-6 sm:p-8 lg:p-10">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.22),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(99,102,241,0.18),transparent_30%)]" />
          <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-200/70 bg-white/70 px-4 py-2 text-sm font-medium text-cyan-700 shadow-sm backdrop-blur">
                <Sparkles size={14} /> Accuracy-focused screening support
              </div>
              <h2 className="mt-5 max-w-2xl text-4xl leading-tight text-slate-950 sm:text-5xl lg:text-6xl">
                AI Diabetes Prediction System with cinematic motion and 3D depth.
              </h2>
              <p className="mt-4 max-w-xl text-base leading-7 text-slate-700 sm:text-lg">
                Submit your health parameters step by step. The interface now uses layered motion graphics, immersive
                intro visuals, and a more polished design system for the prediction workflow.
              </p>
              <div className="mt-5 flex flex-wrap gap-3 text-sm text-slate-700">
                <span className="rounded-full border border-white/70 bg-white/75 px-3 py-1 shadow-sm backdrop-blur"><ShieldCheck size={14} className="mr-1 inline" /> Privacy first</span>
                <span className="rounded-full border border-white/70 bg-white/75 px-3 py-1 shadow-sm backdrop-blur"><Brain size={14} className="mr-1 inline" /> ML-powered</span>
                <span className="rounded-full border border-white/70 bg-white/75 px-3 py-1 shadow-sm backdrop-blur"><Stethoscope size={14} className="mr-1 inline" /> Clinical support only</span>
              </div>
              <div className="mt-7 flex flex-wrap items-center gap-3">
                <a href="#predictor" className="rounded-2xl bg-slate-950 px-5 py-3 font-semibold text-white shadow-lg shadow-slate-950/15 transition hover:-translate-y-0.5">
                  Start Prediction
                </a>
                <a href="#insights" className="rounded-2xl border border-slate-300 bg-white/80 px-5 py-3 font-semibold text-slate-800 shadow-sm transition hover:-translate-y-0.5">
                  View Insights
                </a>
              </div>
              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {[
                  { label: "Predictive flow", value: "3D" },
                  { label: "Motion layers", value: "Live" },
                  { label: "Wellness insights", value: "Always on" },
                ].map((item) => (
                  <motion.div
                    key={item.label}
                    whileHover={{ y: -4 }}
                    className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur"
                  >
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{item.label}</p>
                    <p className="mt-2 text-xl font-semibold text-slate-950">{item.value}</p>
                  </motion.div>
                ))}
              </div>
            </div>
            <motion.div
              initial={{ opacity: 0, scale: 0.94, rotateX: 8 }}
              animate={{ opacity: 1, scale: 1, rotateX: 0 }}
              transition={{ duration: 0.9, ease: "easeOut" }}
              className="relative mx-auto h-[28rem] w-full max-w-[34rem]"
              style={{ perspective: 1500 }}
            >
              <motion.div
                animate={{ rotateX: [12, 6, 12], rotateY: [-14, 10, -14], y: [0, -8, 0] }}
                transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
                className="relative h-full w-full rounded-[2rem] border border-white/80 bg-white/75 p-5 shadow-[0_30px_80px_rgba(15,23,42,0.12)] backdrop-blur-2xl"
                style={{ transformStyle: "preserve-3d" }}
              >
                <div className="absolute inset-0 rounded-[2rem] bg-[linear-gradient(145deg,rgba(255,255,255,0.7),rgba(255,255,255,0.2))]" />
                <div className="absolute inset-6 rounded-[1.5rem] border border-cyan-100/80" />
                <div className="absolute inset-0 rounded-[2rem] bg-[radial-gradient(circle_at_top,rgba(103,232,249,0.16),transparent_40%)]" />

                <motion.div
                  className="absolute left-6 top-6 rounded-2xl border border-white/70 bg-white/85 px-4 py-3 text-xs text-slate-700 shadow-lg shadow-blue-950/5 backdrop-blur"
                  animate={{ y: [0, -10, 0], x: [0, 8, 0] }}
                  transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                  style={{ transform: "translateZ(70px)" }}
                >
                  <p className="uppercase tracking-[0.3em] text-cyan-700">Live signal</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">Adaptive prediction mesh</p>
                </motion.div>

                <motion.div
                  className="absolute right-6 top-14 rounded-2xl border border-white/70 bg-white/85 px-4 py-3 text-xs text-slate-700 shadow-lg shadow-blue-950/5 backdrop-blur"
                  animate={{ y: [0, 8, 0], x: [0, -8, 0] }}
                  transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
                  style={{ transform: "translateZ(50px)" }}
                >
                  <p className="uppercase tracking-[0.3em] text-emerald-700">Risk band</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">Clinically guided motion</p>
                </motion.div>

                <div className="relative flex h-full items-center justify-center">
                  <motion.div
                    className="absolute h-72 w-72 rounded-full border border-cyan-200/70"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
                  />
                  <motion.div
                    className="absolute h-56 w-56 rounded-full border border-white/80"
                    animate={{ rotate: -360 }}
                    transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
                  />
                  <motion.div
                    className="absolute h-40 w-40 rounded-full border border-blue-200/80"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
                  />

                  <motion.div
                    className="absolute h-56 w-56 rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.98),rgba(115,194,255,0.72)_32%,rgba(59,130,246,0.65)_58%,rgba(15,23,42,0.9)_100%)] shadow-[0_0_120px_rgba(56,189,248,0.3)]"
                    animate={{ scale: [1, 1.05, 1], rotate: [0, 8, 0] }}
                    transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    style={{ transform: "translateZ(110px)" }}
                  />

                  <motion.div
                    className="absolute h-20 w-20 rounded-full border border-white/80 bg-white/55 backdrop-blur-md"
                    animate={{ y: [0, -16, 0], x: [0, 14, 0] }}
                    transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
                    style={{ transform: "translate(-140px, -120px) translateZ(90px)" }}
                  />
                  <motion.div
                    className="absolute h-14 w-14 rounded-2xl border border-cyan-100/80 bg-cyan-200/50 backdrop-blur-md"
                    animate={{ y: [0, 18, 0], x: [0, -10, 0] }}
                    transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut" }}
                    style={{ transform: "translate(150px, 100px) translateZ(100px)" }}
                  />

                  <motion.div
                    className="absolute bottom-6 left-6 right-6 rounded-[1.5rem] border border-white/70 bg-white/80 p-4 shadow-xl shadow-slate-950/10 backdrop-blur"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                    style={{ transform: "translateZ(120px)" }}
                  >
                    <div className="flex items-end gap-2">
                      {[34, 58, 44, 72, 55, 80, 67].map((height, index) => (
                        <motion.span
                          key={height}
                          className="w-full rounded-full bg-gradient-to-t from-cyan-400 to-blue-200"
                          animate={{ scaleY: [0.75, 1, 0.8] }}
                          transition={{ duration: 2.8, repeat: Infinity, delay: index * 0.12 }}
                          style={{ height: `${height}px`, transformOrigin: "bottom" }}
                        />
                      ))}
                    </div>
                    <div className="mt-3 flex items-center justify-between text-xs uppercase tracking-[0.28em] text-slate-500">
                      <span>Motion pattern</span>
                      <span>Confidence stream</span>
                    </div>
                  </motion.div>

                  <div className="absolute left-1/2 top-1/2 h-[22rem] w-[22rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/15 blur-3xl" />
                </div>
              </motion.div>
            </motion.div>
          </div>
        </motion.section>

        <section id="insights" className="grid gap-7 lg:grid-cols-3">
          <motion.article {...cardReveal} id="predictor" className="glass rounded-3xl p-6 lg:col-span-2">
            <div className="mb-5 flex items-center justify-between">
              <h3 className="text-2xl">Step-by-step predictor</h3>
              <span className="text-sm font-semibold text-blue-700">{progress}% complete</span>
            </div>
            <div className="mb-6 h-2 rounded-full bg-slate-200">
              <motion.div
                className="h-2 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.25 }}
              />
            </div>

            <form onSubmit={runPrediction}>
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentField.key}
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -25 }}
                  transition={{ duration: 0.25 }}
                  className="rounded-2xl border border-blue-100 bg-white p-5"
                >
                  <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">Step {step + 1} / {fields.length}</p>
                  <h4 className="mt-1 text-2xl">{currentField.label}</h4>
                  <p className="mt-2 text-slate-600">{currentField.tip}</p>
                  {currentField.type === "select" ? (
                    <select
                      value={form[currentField.key]}
                      onChange={(e) => {
                        const value = e.target.value;
                        setForm((prev) => ({ ...prev, [currentField.key]: value }));
                        setErrors((prev) => ({ ...prev, [currentField.key]: validateField(currentField, value) }));
                      }}
                      className="mt-4 w-full rounded-xl border border-slate-300 px-4 py-3 text-lg outline-none transition focus:border-blue-500"
                    >
                      {currentField.options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      min={currentField.min}
                      max={currentField.max}
                      step={currentField.step}
                      value={form[currentField.key]}
                      onChange={(e) => {
                        const value = e.target.value;
                        setForm((prev) => ({ ...prev, [currentField.key]: value }));
                        setErrors((prev) => ({ ...prev, [currentField.key]: validateField(currentField, value) }));
                      }}
                      className="mt-4 w-full rounded-xl border border-slate-300 px-4 py-3 text-lg outline-none transition focus:border-blue-500"
                      placeholder={`Enter ${currentField.label.toLowerCase()}`}
                    />
                  )}
                  <div className="mt-3 flex items-center justify-between">
                    <p className="text-xs text-slate-500">
                      {currentField.type === "select"
                        ? "Tip: you can say male, female, or other."
                        : `Tip: you can speak numbers like "${currentField.label.toLowerCase()} 132".`}
                    </p>
                    <button
                      type="button"
                      disabled={!speechSupported}
                      onClick={() => toggleVoiceInput("field")}
                      className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {listeningTarget === "field" ? <MicOff size={14} /> : <Mic size={14} />}
                      {listeningTarget === "field" ? "Stop" : "Voice Input"}
                    </button>
                  </div>
                  {errors[currentField.key] ? <p className="mt-2 text-sm text-red-500">{errors[currentField.key]}</p> : null}
                </motion.div>
              </AnimatePresence>

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => setStep((s) => Math.max(0, s - 1))}
                  className="rounded-xl border border-slate-300 px-4 py-2 font-medium"
                >
                  Back
                </button>
                {step < fields.length - 1 ? (
                  <button
                    type="button"
                    onClick={handleStepNext}
                    className="rounded-xl bg-blue-600 px-5 py-2 font-medium text-white"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={loadingPrediction}
                    className="rounded-xl bg-blue-600 px-5 py-2 font-medium text-white disabled:opacity-60"
                  >
                    {loadingPrediction ? "Analyzing..." : "Predict Risk"}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => {
                    setForm(defaultPayload);
                    setStep(0);
                    setResult(null);
                    setErrors({});
                  }}
                  className="rounded-xl border border-slate-300 px-4 py-2 font-medium"
                >
                  Reset
                </button>
              </div>
            </form>
          </motion.article>

          <motion.article {...cardReveal} className="glass rounded-3xl p-6">
            <h3 className="text-2xl">Account</h3>
            {user ? (
              <div className="mt-4 space-y-2 text-sm">
                <p className="font-semibold text-blue-700">Signed in as {user.username}</p>
                <p>{user.full_name || "No full name yet"}</p>
                <p>{user.email || ""}</p>
                <p className="rounded-xl bg-emerald-100 px-3 py-2 text-emerald-700">Prediction history is saved automatically.</p>
              </div>
            ) : (
              <>
                <p className="mt-4 rounded-xl bg-cyan-50 px-3 py-2 text-sm text-cyan-800">
                  Guest mode enabled: your last 50 predictions are stored only on this browser.
                </p>
                <form onSubmit={submitAuth} className="mt-4 space-y-3">
                  <div className="flex rounded-xl border border-slate-300 p-1 text-sm">
                    <button type="button" onClick={() => setAuthMode("login")} className={`w-1/2 rounded-lg py-2 ${authMode === "login" ? "bg-blue-600 text-white" : ""}`}>Login</button>
                    <button type="button" onClick={() => setAuthMode("signup")} className={`w-1/2 rounded-lg py-2 ${authMode === "signup" ? "bg-blue-600 text-white" : ""}`}>Signup</button>
                  </div>
                  <input className="w-full rounded-xl border border-slate-300 px-3 py-2" placeholder="Username" value={authForm.username} onChange={(e) => setAuthForm((p) => ({ ...p, username: e.target.value }))} required />
                  {authMode === "signup" ? <input className="w-full rounded-xl border border-slate-300 px-3 py-2" placeholder="Email" value={authForm.email} onChange={(e) => setAuthForm((p) => ({ ...p, email: e.target.value }))} required type="email" /> : null}
                  {authMode === "signup" ? <input className="w-full rounded-xl border border-slate-300 px-3 py-2" placeholder="Full name" value={authForm.full_name} onChange={(e) => setAuthForm((p) => ({ ...p, full_name: e.target.value }))} /> : null}
                  <input className="w-full rounded-xl border border-slate-300 px-3 py-2" placeholder="Password" value={authForm.password} onChange={(e) => setAuthForm((p) => ({ ...p, password: e.target.value }))} required type="password" />
                  <button className="w-full rounded-xl bg-blue-600 px-3 py-2 font-semibold text-white">{authMode === "login" ? "Login" : "Create account"}</button>
                </form>
              </>
            )}
          </motion.article>
        </section>

        {result ? (
          <motion.section {...cardReveal} className="glass rounded-3xl p-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <p className="text-sm uppercase tracking-widest text-slate-500">Prediction Result</p>
                <h3 className={`mt-2 text-3xl ${riskColor}`}>
                  {result.risk_level === "high" ? "High Risk" : result.risk_level === "medium" ? "Moderate Risk" : "Low Risk"}
                </h3>
                <p className="mt-2 text-slate-700">
                  Model output: <strong>{result.prediction}</strong>{" "}
                  {result.confidence !== null && result.confidence !== undefined
                    ? `with ${confidencePercent}% confidence.`
                    : "without probability score."}
                </p>
                {result.model_version ? (
                  <p className="mt-1 text-xs text-slate-500">Model version: {result.model_version}</p>
                ) : null}
                {result.emergency_notice ? (
                  <p className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {result.emergency_notice}
                  </p>
                ) : null}
                {result.warnings?.length ? (
                  <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4">
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-amber-700">Safety Flags</h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-amber-800">
                      {result.warnings.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                <div className="mt-4 rounded-2xl bg-white p-4">
                  <h4 className="text-lg">Smart Recommendations</h4>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700">
                    {(result.suggestions || []).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                {result.action_plan_7d?.length ? (
                  <div className="mt-4 rounded-2xl bg-white p-4">
                    <h4 className="text-lg">7-Day Action Plan</h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700">
                      {result.action_plan_7d.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {result.explanation_factors?.length ? (
                  <div className="mt-4 rounded-2xl bg-white p-4">
                    <h4 className="text-lg">Why This Prediction</h4>
                    <div className="mt-2 space-y-2">
                      {result.explanation_factors.map((factor) => (
                        <div key={factor.feature} className="rounded-xl border border-slate-200 px-3 py-2 text-sm">
                          <p className="font-semibold text-slate-800">{factor.label}: {factor.value}</p>
                          <p className="text-slate-600">
                            {factor.direction} compared to model baseline (z-score: {factor.z_score}).
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">Confidence Gauge</p>
                <div className="mx-auto mt-4 grid h-40 w-40 place-content-center rounded-full border-[12px] border-slate-100" style={{ background: `conic-gradient(#e5484d ${Math.min(confidencePercent, 100) * 3.6}deg, #e2e8f0 0deg)` }}>
                  <div className="grid h-28 w-28 place-content-center rounded-full bg-white text-3xl font-bold text-blue-700">{confidencePercent}%</div>
                </div>
                <p className="mt-3 text-xs uppercase tracking-widest text-slate-500">Confidence Band</p>
                <p className="text-sm font-semibold text-slate-700">{result.confidence_band || "unknown"}</p>
              </div>
            </div>
          </motion.section>
        ) : null}

        <section className="grid gap-7 lg:grid-cols-3">
          <motion.article {...cardReveal} className="glass rounded-3xl p-6 lg:col-span-2">
            <div className="mb-4 flex items-center gap-2"><TrendingUp size={18} /><h3 className="text-2xl">Risk Trend Dashboard</h3></div>
            <div className="mb-4 rounded-xl bg-white p-3 text-sm text-slate-700">
              <p className="font-semibold text-blue-700">Trend: {trendSummary.label}</p>
              <p>{trendSummary.detail}</p>
            </div>
            {history.length === 0 ? (
              <p className="rounded-2xl bg-white p-4 text-slate-600">Run predictions to build your timeline. Login syncs history across sessions.</p>
            ) : (
              <div className="h-72 rounded-2xl bg-white p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="confidence" stroke="#1976d2" strokeWidth={3} dot={{ r: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </motion.article>

          <motion.article {...cardReveal} className="glass rounded-3xl p-6">
            <div className="mb-4 flex items-center gap-2"><Bot size={18} /><h3 className="text-2xl">AI Chatbot</h3></div>
            <div className="h-56 space-y-2 overflow-y-auto rounded-2xl bg-white p-3">
              {chatMessages.map((msg, idx) => (
                <div key={`${msg.role}-${idx}`} className={`max-w-[90%] rounded-xl px-3 py-2 text-sm ${msg.role === "assistant" ? "bg-slate-100" : "ml-auto bg-blue-600 text-white"}`}>
                  {msg.content}
                </div>
              ))}
            </div>
            <div className="mt-3 flex gap-2">
              <input
                value={chatQuestion}
                onChange={(e) => setChatQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void askAssistant();
                  }
                }}
                placeholder="Ask about diet, exercise, result..."
                className="w-full rounded-xl border border-slate-300 px-3 py-2"
              />
              <button
                onClick={() => toggleVoiceInput("chat")}
                disabled={!speechSupported}
                className="rounded-xl border border-slate-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
                title="Voice input"
              >
                {listeningTarget === "chat" ? <MicOff size={16} /> : <Mic size={16} />}
              </button>
              <button onClick={askAssistant} disabled={chatLoading} className="rounded-xl bg-blue-600 px-3 py-2 text-white">{chatLoading ? "..." : "Ask"}</button>
            </div>
            {!speechSupported ? <p className="mt-2 text-xs text-slate-500">Voice input is not supported in this browser.</p> : null}
          </motion.article>
        </section>

        {user ? (
          <UserStore user={user} />
        ) : null}

        {user ? (
          <HealthcareManagement user={user} />
        ) : null}

        {user ? (
          <motion.section {...cardReveal} className="glass rounded-3xl p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Database size={18} />
                <h3 className="text-2xl">Admin Dashboard</h3>
              </div>
              <button
                type="button"
                onClick={loadAdminOverview}
                disabled={loadingAdminOverview}
                className="rounded-xl border border-slate-300 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"
              >
                {loadingAdminOverview ? "Refreshing..." : "Refresh data"}
              </button>
            </div>

            {adminOverviewError ? (
              <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{adminOverviewError}</p>
            ) : null}

            {!user?.is_admin ? (
              <p className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                Admin access is required to view dashboard metrics. This account is currently a standard user.
              </p>
            ) : adminOverview?.overview ? (
              <>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Users</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">{adminOverview.overview.total_users}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Assessments</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">{adminOverview.overview.total_assessments}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Diabetic</p>
                    <p className="mt-2 text-2xl font-semibold text-red-600">{adminOverview.overview.diabetic_assessments}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Non-Diabetic</p>
                    <p className="mt-2 text-2xl font-semibold text-emerald-600">{adminOverview.overview.non_diabetic_assessments}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Bookings</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">{adminOverview.overview.nutritionist_bookings}</p>
                  </div>
                </div>

                <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
                  <h4 className="text-lg font-semibold text-slate-900">14-Day Assessment Trend</h4>
                  {adminTrendData.length ? (
                    <div className="mt-3 h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={adminTrendData}>
                          <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                          <Tooltip />
                          <Bar dataKey="total" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="diabetic" fill="#ef4444" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-600">No trend data available in the last 14 days yet.</p>
                  )}
                </div>

                <div className="mt-5 grid gap-5 lg:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <h4 className="text-lg font-semibold text-slate-900">Database Storage Overview</h4>
                    <p className="mt-2 text-sm text-slate-700">
                      Your app data is stored in a local SQLite database on the backend server.
                    </p>
                    <div className="mt-3 space-y-1 text-sm text-slate-700">
                      <p><strong>Type:</strong> {adminOverview.storage?.database_type || "SQLite"}</p>
                      <p><strong>Path:</strong> {adminOverview.storage?.database_path || "N/A"}</p>
                      <p><strong>Size:</strong> {adminOverview.storage?.database_size_mb ?? 0} MB</p>
                    </div>
                    <div className="mt-3">
                      <p className="text-sm font-semibold text-slate-800">Main tables:</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(adminOverview.storage?.tables || []).map((tableName) => (
                          <span
                            key={tableName}
                            className="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700"
                          >
                            {tableName}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <h4 className="text-lg font-semibold text-slate-900">Recent Assessments</h4>
                    {adminOverview.recent_assessments?.length ? (
                      <div className="mt-3 overflow-x-auto">
                        <table className="w-full min-w-[28rem] text-left text-sm">
                          <thead className="text-xs uppercase tracking-wider text-slate-500">
                            <tr>
                              <th className="pb-2">ID</th>
                              <th className="pb-2">User</th>
                              <th className="pb-2">Prediction</th>
                              <th className="pb-2">Confidence</th>
                              <th className="pb-2">Created</th>
                            </tr>
                          </thead>
                          <tbody>
                            {adminOverview.recent_assessments.map((row) => (
                              <tr key={row.id} className="border-t border-slate-100">
                                <td className="py-2 pr-2 font-semibold text-slate-800">#{row.id}</td>
                                <td className="py-2 pr-2">{row.user_id}</td>
                                <td className="py-2 pr-2">{row.prediction}</td>
                                <td className="py-2 pr-2">
                                  {row.confidence !== null && row.confidence !== undefined
                                    ? `${Math.round(row.confidence * 100)}%`
                                    : "N/A"}
                                </td>
                                <td className="py-2 pr-2">{new Date(row.created_at).toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-slate-600">No assessments have been stored yet.</p>
                    )}
                  </div>
                </div>

                <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
                  <h4 className="text-lg font-semibold text-slate-900">Recent Login Activity</h4>
                  {adminOverview.recent_auth_activity?.length ? (
                    <div className="mt-3 overflow-x-auto">
                      <table className="w-full min-w-[42rem] text-left text-sm">
                        <thead className="text-xs uppercase tracking-wider text-slate-500">
                          <tr>
                            <th className="pb-2">Time</th>
                            <th className="pb-2">User</th>
                            <th className="pb-2">Event</th>
                            <th className="pb-2">Status</th>
                            <th className="pb-2">IP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {adminOverview.recent_auth_activity.map((row) => (
                            <tr key={row.id} className="border-t border-slate-100">
                              <td className="py-2 pr-3">{new Date(row.created_at).toLocaleString()}</td>
                              <td className="py-2 pr-3">{row.username || `User #${row.user_id || "N/A"}`}</td>
                              <td className="py-2 pr-3">{row.event_type}</td>
                              <td className="py-2 pr-3">{row.status}</td>
                              <td className="py-2 pr-3">{row.ip_address || "N/A"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-600">No login activity recorded yet.</p>
                  )}
                </div>

                <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
                  <h4 className="text-lg font-semibold text-slate-900">Users and Their Data</h4>
                  {adminOverview.users_data?.length ? (
                    <div className="mt-3 overflow-x-auto">
                      <table className="w-full min-w-[64rem] text-left text-sm">
                        <thead className="text-xs uppercase tracking-wider text-slate-500">
                          <tr>
                            <th className="pb-2">User</th>
                            <th className="pb-2">Email</th>
                            <th className="pb-2">Assessments</th>
                            <th className="pb-2">Diabetic Cases</th>
                            <th className="pb-2">Latest Prediction</th>
                            <th className="pb-2">Latest Confidence</th>
                            <th className="pb-2">Latest Glucose</th>
                            <th className="pb-2">Latest BMI</th>
                            <th className="pb-2">Bookings</th>
                            <th className="pb-2">Last Assessment</th>
                          </tr>
                        </thead>
                        <tbody>
                          {adminOverview.users_data.map((u) => (
                            <tr key={u.id} className="border-t border-slate-100 align-top">
                              <td className="py-2 pr-3">
                                <p className="font-semibold text-slate-800">{u.full_name || u.username}</p>
                                <p className="text-xs text-slate-500">@{u.username} #{u.id}</p>
                                {u.is_admin ? (
                                  <span className="mt-1 inline-flex rounded-full border border-cyan-300 bg-cyan-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-cyan-700">
                                    Admin
                                  </span>
                                ) : null}
                              </td>
                              <td className="py-2 pr-3 text-slate-700">{u.email}</td>
                              <td className="py-2 pr-3 font-semibold text-slate-800">{u.assessment_count || 0}</td>
                              <td className="py-2 pr-3 text-red-600">{u.diabetic_count || 0}</td>
                              <td className="py-2 pr-3">{u.latest_prediction || "N/A"}</td>
                              <td className="py-2 pr-3">
                                {u.latest_confidence !== null && u.latest_confidence !== undefined
                                  ? `${Math.round(u.latest_confidence * 100)}%`
                                  : "N/A"}
                              </td>
                              <td className="py-2 pr-3">{u.latest_glucose ?? "N/A"}</td>
                              <td className="py-2 pr-3">{u.latest_bmi ?? "N/A"}</td>
                              <td className="py-2 pr-3">{u.booking_count || 0}</td>
                              <td className="py-2 pr-3">{u.last_assessment_at ? new Date(u.last_assessment_at).toLocaleString() : "No records"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-600">No users found in the database yet.</p>
                  )}
                </div>
              </>
            ) : (
              <p className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
                {loadingAdminOverview
                  ? "Loading admin data..."
                  : "No admin overview available yet. Click Refresh data."}
              </p>
            )}
          </motion.section>
        ) : null}

        <motion.section {...cardReveal} className="glass rounded-3xl p-5 text-sm text-slate-700">
          <h4 className="text-lg">Trust and Safety</h4>
          <p className="mt-2">
            This assistant provides decision support and wellness guidance. It is not a diagnosis. Always consult a qualified clinician for medical decisions.
          </p>
          <p className="mt-2">Model confidence can vary by population and input quality. Use recent, accurate measurements for better predictions.</p>
        </motion.section>
      </main>
    </div>
  );
}

export default App;
