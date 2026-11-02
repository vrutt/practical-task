"use client";
import "@/assets/css/auth-form.css";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { SubmitEvent } from "react";
import { useState } from "react";

import { authService } from "@/services/api/apiCalls/auth";
import { errorMessage } from "@/services/api/client";
import { useAuth } from "@/store/auth";
import type { IAuthFormProps } from "@/types/auth";
import { passwordPattern, passwordRequirements } from "@/utils/constants";

export default function AuthForm({ registration = false }: IAuthFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const setUser = useAuth((s) => s.setUser);
  const router = useRouter();
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (registration && !name.trim()) {
        setError("Please enter your name.");
        return;
      }
      if (registration && !passwordPattern.test(password)) {
        setError(passwordRequirements);
        return;
      }
      if (registration) {
        await authService.register({ name: name.trim(), email, password });
        router.replace("/login?registered=1");
      } else {
        setUser(await authService.login({ email, password }));
        router.replace("/dashboard");
      }
    } catch (error) {
      setError(errorMessage(error, "Unable to reach the server. Please try again."));
    } finally {
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
          <button disabled={busy}>
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
