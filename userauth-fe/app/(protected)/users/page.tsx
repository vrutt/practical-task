"use client";
import "@/assets/css/users.css";

import { useEffect, useState } from "react";

import { authService } from "@/services/api/apiCalls/auth";
import { errorMessage } from "@/services/api/client";
import { useAuth } from "@/store/auth";
import type { IUser } from "@/types/auth";

export default function UsersPage() {
  const user = useAuth((s) => s.user);
  const [users, setUsers] = useState<IUser[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const users = await authService.listUsers();
        if (active) setUsers(users);
      } catch (error) {
        if (active) setError(errorMessage(error, "Unable to load users. Please try again."));
      }
    }
    if (user) void load();
    return () => {
      active = false;
    };
  }, [user]);
  return (
    <>
      <p className="eyebrow">ADMINISTRATION</p>
      <h1>Users</h1>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!error && !users && <p role="status">Loading users…</p>}
      {users && (
        <section className="card users-list">
          <ul>
            {users.map((item) => (
              <li key={item.id}>
                {item.name} · {item.email} · {item.role}
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
