import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { loginUser } from "../api";
import { useAuth } from "../auth";

interface RegistrationState { registeredEmail?: string }

export default function LoginPage() {
  const location = useLocation();
  const registeredEmail = (location.state as RegistrationState | null)?.registeredEmail ?? "";
  const [email, setEmail] = useState(registeredEmail);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { user, signIn } = useAuth();
  if (user) return <Navigate to="/products" replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(""); setSubmitting(true);
    try { signIn(await loginUser(email, password)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Login failed"); }
    finally { setSubmitting(false); }
  };

  return <div className="form-page"><section className="account-card">
    <span className="eyebrow">Welcome back</span><h1>Log in</h1>
    {registeredEmail && <div className="form-success" role="status">Account created. You can log in now.</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <form onSubmit={submit}>
      <label>Email address<input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      <button className="button" type="submit" disabled={submitting}>{submitting ? "Logging in…" : "Log in"}</button>
    </form>
    <p className="form-switch">New here? <Link to="/create-account">Create an account</Link></p>
  </section></div>;
}
