import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  Bot,
  Brain,
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
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api";

const fields = [
  { key: "pregnancies", label: "Pregnancies", min: 0, max: 20, step: 1, tip: "Total number of pregnancies." },
  { key: "glucose", label: "Glucose", min: 0, max: 300, step: 1, tip: "Plasma glucose concentration." },
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

function saveGuestHistoryToStorage(entries) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(GUEST_HISTORY_KEY, JSON.stringify(entries.slice(0, 50)));
}

const cardReveal = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: "easeOut" },
};

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
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content: "I am your AI wellness assistant. Ask me about your result, food, exercise, or diabetes prevention.",
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

  function validateField(field, value) {
    if (value === "") return "This field is required.";
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
      Object.entries(form).map(([key, value]) => [key, Number(value)])
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
      if (authMode === "login") {
        const data = await api.login({ username: authForm.username, password: authForm.password });
        setUser({ username: data.username, email: data.email, full_name: data.full_name });
      } else {
        await api.register(authForm);
        const session = await api.checkSession();
        setUser(session.user || null);
      }
      setAuthForm({ username: "", email: "", password: "", full_name: "" });
      await loadHistory();
    } catch (error) {
      alert(error.message);
    }
  }

  async function handleLogout() {
    await api.logout().catch(() => null);
    setUser(null);
    setHistory(loadGuestHistoryFromStorage());
  }

  async function askAssistant() {
    if (!chatQuestion.trim()) return;
    const nextMessages = [...chatMessages, { role: "user", content: chatQuestion }];
    setChatMessages(nextMessages);
    setChatQuestion("");
    setChatLoading(true);

    try {
      const data = await api.chatbot({
        question: chatQuestion,
        risk_level: result?.risk_level || "",
        glucose: form.glucose,
        bmi: form.bmi,
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
        const match = transcript.match(/-?\d+(\.\d+)?/);
        const spokenValue = match ? match[0] : "";
        setForm((prev) => ({ ...prev, [currentField.key]: spokenValue }));
        setErrors((prev) => ({
          ...prev,
          [currentField.key]: validateField(currentField, spokenValue),
        }));
      }

      if (target === "chat") {
        setChatQuestion(transcript);
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

  const confidencePercent = result?.confidence ? Math.round(result.confidence * 100) : 0;
  const riskColor =
    result?.risk_level === "high"
      ? "text-red-500"
      : result?.risk_level === "medium"
      ? "text-amber-500"
      : "text-emerald-500";

  return (
    <div className="pb-14">
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-2 text-white">
              <HeartPulse size={18} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">AI Medical Assistant</p>
              <h1 className="text-lg font-bold">Diabetes Prediction Dashboard</h1>
            </div>
          </div>
          {user ? (
            <button onClick={handleLogout} className="flex items-center gap-2 rounded-full border border-slate-300 px-3 py-1 text-sm">
              <LogOut size={14} /> Logout
            </button>
          ) : null}
        </div>
      </header>

      <main className="mx-auto mt-6 max-w-6xl space-y-7 px-4 sm:px-6">
        <motion.section {...cardReveal} className="glass grid-fade overflow-hidden rounded-3xl p-6 sm:p-9">
          <div className="grid gap-7 md:grid-cols-2 md:items-center">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
                <Sparkles size={14} /> Accuracy-focused screening support
              </div>
              <h2 className="text-4xl leading-tight">AI Diabetes Prediction System</h2>
              <p className="mt-3 text-slate-700">
                Submit your health parameters step by step. Our machine learning model predicts risk level, confidence,
                and gives personalized recommendations.
              </p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-700">
                <span className="rounded-full bg-white px-3 py-1"><ShieldCheck size={14} className="mr-1 inline" /> Privacy first</span>
                <span className="rounded-full bg-white px-3 py-1"><Brain size={14} className="mr-1 inline" /> ML-powered</span>
                <span className="rounded-full bg-white px-3 py-1"><Stethoscope size={14} className="mr-1 inline" /> Clinical support only</span>
              </div>
              <a href="#predictor" className="mt-6 inline-block rounded-2xl bg-blue-600 px-5 py-3 font-semibold text-white shadow-lg shadow-blue-600/25">
                Start Prediction
              </a>
            </div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8 }}
              className="relative mx-auto h-64 w-full max-w-md rounded-3xl border border-white/70 bg-gradient-to-br from-cyan-50 via-white to-blue-100 p-6"
            >
              <div className="absolute -left-6 -top-6 h-24 w-24 rounded-full bg-cyan-300/45 blur-2xl" />
              <div className="absolute -bottom-7 right-6 h-24 w-24 rounded-full bg-blue-300/45 blur-2xl" />
              <div className="relative grid h-full place-content-center rounded-2xl border border-blue-100 bg-white/80 text-center">
                <Activity className="mx-auto text-blue-600" size={46} />
                <p className="mt-3 text-sm font-semibold text-slate-500">Adaptive risk pattern analysis</p>
                <p className="text-3xl font-bold text-blue-700">24/7</p>
              </div>
            </motion.div>
          </div>
        </motion.section>

        <section className="grid gap-7 lg:grid-cols-3">
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
                  <div className="mt-3 flex items-center justify-between">
                    <p className="text-xs text-slate-500">Tip: you can speak numbers like "glucose 132".</p>
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
                  Model output: <strong>{result.prediction}</strong> {result.confidence ? `with ${confidencePercent}% confidence.` : "without probability score."}
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
              <input value={chatQuestion} onChange={(e) => setChatQuestion(e.target.value)} placeholder="Ask about diet, exercise, result..." className="w-full rounded-xl border border-slate-300 px-3 py-2" />
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
