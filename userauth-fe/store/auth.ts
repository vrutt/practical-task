import { create } from "zustand";

import type { IAuthState } from "@/types/auth";

export const useAuth = create<IAuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
