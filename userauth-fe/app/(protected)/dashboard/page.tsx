"use client";
import "@/assets/css/dashboard.css";

import Link from "next/link";

import { useAuth } from "@/store/auth";
export default function Dashboard() {
  const user = useAuth((s) => s.user);
  return (
    <>
      <p className="eyebrow">DASHBOARD</p>
      <h1>Welcome, {user?.name}</h1>
      <p className="muted">
        You are signed in. Your account information is available on your profile.
      </p>
      <Link className="dashboard-link" href="/profile">
        View profile →
      </Link>
    </>
  );
}
