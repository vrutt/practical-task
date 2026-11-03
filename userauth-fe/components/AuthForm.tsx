"use client";


import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { SubmitEvent } from "react";
import { Suspense, useRef, useState } from "react";

import type { IAuthFormProps } from "@/types/auth";

import { authService } from "@/services/api/apiCalls/auth";
import { errorMessage } from "@/services/api/client";

import { useAuth } from "@/store/auth";
import { passwordPattern, passwordRequirements } from "@/utils/constants";
import "@/assets/css/auth-form.css";

function RegisteredNotice() {
  const registered = useSearchParams().get("registered") === "1";
  if (!registered) return null;
  return (
    <p role="status" className="auth-success">
      Account created. Sign in to continue.
    </p>
  );
}

export default function AuthForm({ registration = false }: IAuthFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const setUser = useAuth((s) => s.setUser);
  const router = useRouter();
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setError("");
    setBusy(true);
    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    try {
      if (!trimmedEmail) {
        setError("Please enter your email.");
        return;
      }
      if (registration && !trimmedName) {
        setError("Please enter your name.");
        return;
      }
      if (registration && !passwordPattern.test(password)) {
        setError(passwordRequirements);
        return;
      }
      if (registration) {
        await authService.register({ name: trimmedName, email: trimmedEmail, password });
        router.replace("/login?registered=1");
      } else {
        const user = await authService.login({ email: trimmedEmail, password });
        setUser(user);
        router.replace(user.role === "Admin" ? "/users" : "/dashboard");
      }
    } catch (error) {
      setError(errorMessage(error, "Unable to reach the server. Please try again."));
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  return (
    <main className="center">
      <section className="card">
        <p className="eyebrow">ACCOUNT ACCESS</p>
        <h1>{registration ? "Create your account" : "Welcome back"}</h1>
        <p className="muted">
          {registration ? "Enter your details to get started." : "Sign in to access your account."}
        </p>
        {!registration && (
          <Suspense fallback={null}>
            <RegisteredNotice />
          </Suspense>
        )}
        <form className="auth-form" onSubmit={submit}>
          {registration && (
            <label>
              Name
              <input
                autoComplete="name"
                required
                maxLength={100}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
          )}
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              required
              maxLength={255}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete={registration ? "new-password" : "current-password"}
              required
              minLength={registration ? 8 : 1}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {registration && <small>{passwordRequirements}</small>}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <button type="submit" disabled={busy}>
            {busy ? "Please wait…" : registration ? "Create account" : "Sign in"}
          </button>
        </form>
        <p className="muted">
          {registration ? "Already have an account? " : "New here? "}
          <Link href={registration ? "/login" : "/register"}>
            {registration ? "Sign in" : "Create an account"}
          </Link>
        </p>
      </section>
    </main>
  );
}
