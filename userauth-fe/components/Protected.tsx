"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import type { IProtectedProps, IUser } from "@/types/auth";

import { ApiError } from "@/services/api/client";
import { authService } from "@/services/api/apiCalls/auth";

import { useAuth } from "@/store/auth";

import "@/assets/css/protected.css";

const ADMIN_ROUTE = "/users";

function isAllowed(pathname: string, role: IUser["role"]) {
  const adminRoute = pathname === ADMIN_ROUTE || pathname.startsWith(`${ADMIN_ROUTE}/`);
  return !adminRoute || role === "Admin";
}

export default function Protected({ children }: IProtectedProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [signingOut, setSigningOut] = useState(false);
  const logoutLock = useRef(false);
  const setUser = useAuth((s) => s.setUser);
  const user = useAuth((s) => s.user);
  const denied = Boolean(ready && user && !isAllowed(pathname, user.role));
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const current = await authService.currentUser();
        if (!active) return;
        setUser(current);
        setError("");
        setReady(true);
      } catch (error) {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          setUser(null);
          router.replace("/login");
          return;
        }
        setReady(false);
        setError("Unable to load your account. Check your connection and try again.");
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [attempt, router, setUser]);
  useEffect(() => {
    if (denied) router.replace("/dashboard");
  }, [denied, router]);
  async function logout() {
    if (logoutLock.current) return;
    logoutLock.current = true;
    setSigningOut(true);
    setError("");
    try {
      await authService.logout();
      setUser(null);
      router.replace("/login");
    } catch {
      logoutLock.current = false;
      setSigningOut(false);
      setError("Could not sign out. Please try again.");
    }
  }
  function retry() {
    setError("");
    setReady(false);
    setAttempt((value) => value + 1);
  }
  if (!ready)
    return (
      <main className="center">
        <section className="card session-gate">
          {error ? (
            <>
              <p role="alert" className="error">
                {error}
              </p>
              <button type="button" onClick={retry}>
                Try again
              </button>
            </>
          ) : (
            <p role="status">Loading your account…</p>
          )}
        </section>
      </main>
    );
  return (
    <>
      <header className="protected-header">
        <Link href="/dashboard" className="brand">
          Account
        </Link>
        <nav>
          <Link href="/dashboard">Dashboard</Link>
          <Link href="/profile">Profile</Link>
          {user?.role === "Admin" && <Link href="/users">Users</Link>}
          <button className="secondary" type="button" disabled={signingOut} onClick={logout}>
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </nav>
      </header>
      <main className="content">
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {denied ? <p role="status">Redirecting to your dashboard…</p> : children}
      </main>
    </>
  );
}
