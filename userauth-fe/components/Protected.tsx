"use client";
import "@/assets/css/protected.css";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { authService } from "@/services/api/apiCalls/auth";
import { ApiError } from "@/services/api/client";
import { useAuth } from "@/store/auth";
import type { IProtectedProps } from "@/types/auth";

export default function Protected({ children }: IProtectedProps) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const setUser = useAuth((s) => s.setUser);
  const user = useAuth((s) => s.user);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const user = await authService.currentUser();
        if (active) {
          setUser(user);
          setReady(true);
        }
      } catch (error) {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          setUser(null);
          router.replace("/login");
          return;
        }
        setError("Unable to load your account. Check your connection and try again.");
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [router, setUser]);
  async function logout() {
    try {
      await authService.logout();
      setUser(null);
      router.replace("/login");
    } catch {
      setError("Could not sign out. Please try again.");
    }
  }
  if (!ready)
    return (
      <main className="center">
        <p role="status">{error || "Loading your account…"}</p>
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
          <button className="secondary" onClick={logout}>
            Sign out
          </button>
        </nav>
      </header>
      <main className="content">
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {children}
      </main>
    </>
  );
}
