import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { registerUser } from "../api";
import { useAuth } from "../auth";

export default function AccountPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  if (user) return <Navigate to="/products" replace />;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setError("");
    const data = new FormData(event.currentTarget);
    const payload = {
      first_name: String(data.get("first_name") ?? ""), last_name: String(data.get("last_name") ?? ""),
      email: String(data.get("email") ?? ""), password: String(data.get("password") ?? ""),
      password_confirmation: String(data.get("password_confirmation") ?? ""),
    };
    if (payload.password !== payload.password_confirmation) { setError("Passwords do not match"); return; }
    setSubmitting(true);
    try { await registerUser(payload); navigate("/login", { replace: true, state: { registeredEmail: payload.email } }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Account creation failed"); }
    finally { setSubmitting(false); }
  };

  return <div className="form-page"><section className="account-card">
    <span className="eyebrow">Join the community</span><h1>Create account</h1><p>Save your details for a faster, more personal Campus Customs experience.</p>
    {error && <div className="form-error" role="alert">{error}</div>}
    <form onSubmit={submit}>
      <div className="field-row"><label>First name<input name="first_name" autoComplete="given-name" maxLength={80} required /></label><label>Last name<input name="last_name" autoComplete="family-name" maxLength={80} required /></label></div>
      <label>Email address<input name="email" type="email" autoComplete="email" maxLength={254} required /></label>
      <label>Password<input name="password" type="password" autoComplete="new-password" minLength={8} maxLength={128} required /><small>Use at least 8 characters.</small></label>
      <label>Confirm password<input name="password_confirmation" type="password" autoComplete="new-password" minLength={8} maxLength={128} required /></label>
      <button className="button" type="submit" disabled={submitting}>{submitting ? "Creating account…" : "Create account"}</button>
    </form>
    <p className="form-switch">Already registered? <Link to="/login">Log in</Link></p>
  </section></div>;
}
