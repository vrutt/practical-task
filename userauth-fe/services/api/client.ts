import { API_ENDPOINTS } from "@/services/api/endpoints";
import type {
  IApiRequestOptions,
  IErrorResponse,
  ISuccessResponse,
  IValidationError,
} from "@/types";

const API_PREFIX = "/api/v1";
const FALLBACK_MESSAGE = "Please check your details and try again.";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly errors: IValidationError[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshing: Promise<boolean> | null = null;

function refreshSession(): Promise<boolean> {
  if (!refreshing) {
    refreshing = fetch(`${API_PREFIX}${API_ENDPOINTS.auth.refresh}`, {
      method: "POST",
      credentials: "same-origin",
    })
      .then((response) => {
        if (response.status >= 500) throw new Error("Server error");
        return response.ok;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

async function errorFrom(response: Response): Promise<ApiError> {
  const body: Partial<IErrorResponse> | null = await response.json().catch(() => null);
  const errors = Array.isArray(body?.errors) ? body.errors : [];
  const message = errors.length
    ? `${errors[0].field}: ${errors[0].message}`
    : body?.message || FALLBACK_MESSAGE;
  return new ApiError(response.status, message, errors);
}

export async function apiRequest<T>(path: string, options: IApiRequestOptions = {}): Promise<T> {
  const { refreshOnUnauthorized = false, ...requestOptions } = options;
  const send = () =>
    fetch(`${API_PREFIX}${path}`, {
      ...requestOptions,
      credentials: "same-origin",
      cache: "no-store",
    });
  let response = await send();
  if (response.status === 401 && refreshOnUnauthorized && (await refreshSession()))
    response = await send();
  if (!response.ok) throw await errorFrom(response);
  const body = (await response.json()) as ISuccessResponse<T>;
  return body.data;
}

export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}
