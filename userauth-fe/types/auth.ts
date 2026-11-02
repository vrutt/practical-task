import type { ReactNode } from "react";

export interface IAuthFormProps {
  registration?: boolean;
}

export interface IProtectedProps {
  children: ReactNode;
}

export interface IUser {
  id: string;
  name: string;
  email: string;
  created_at: string;
  role: "Admin" | "User";
}

export interface ILoginPayload {
  email: string;
  password: string;
}

export interface IRegisterPayload extends ILoginPayload {
  name: string;
}

export interface IAuthState {
  user: IUser | null;
  setUser: (user: IUser | null) => void;
}
