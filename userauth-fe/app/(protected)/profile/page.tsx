"use client";

import { useAuth } from "@/store/auth";

import "@/assets/css/profile.css";

export default function Profile() {
  const user = useAuth((s) => s.user);
  return (
    <>
      <p className="eyebrow">YOUR ACCOUNT</p>
      <h1>Profile</h1>
      <section className="card profile">
        <dl>
          <dt>Name</dt>
          <dd>{user?.name}</dd>
          <dt>Email</dt>
          <dd>{user?.email}</dd>
          <dt>Role</dt>
          <dd>{user?.role}</dd>
          <dt>Member since</dt>
          <dd>
            {user && new Date(user.created_at).toLocaleDateString(undefined, { dateStyle: "long" })}
          </dd>
        </dl>
      </section>
    </>
  );
}
