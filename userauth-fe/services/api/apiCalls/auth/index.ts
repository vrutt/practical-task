import type { ILoginPayload, IRegisterPayload, IUser } from "@/types/auth";

import { apiRequest } from "@/services/api/client";
import { API_ENDPOINTS } from "@/services/api/endpoints";


const jsonHeaders = { "Content-Type": "application/json" };

export const authService = {
  register(payload: IRegisterPayload): Promise<IUser> {
    return apiRequest<IUser>(API_ENDPOINTS.auth.register, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });
  },
  login(payload: ILoginPayload): Promise<IUser> {
    return apiRequest<IUser>(API_ENDPOINTS.auth.login, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });
  },
  currentUser(): Promise<IUser> {
    return apiRequest<IUser>(API_ENDPOINTS.auth.me, { refreshOnUnauthorized: true });
  },
  listUsers(): Promise<IUser[]> {
    return apiRequest<IUser[]>(API_ENDPOINTS.auth.users, { refreshOnUnauthorized: true });
  },
  logout(): Promise<null> {
    return apiRequest<null>(API_ENDPOINTS.auth.logout, { method: "POST" });
  },
};
