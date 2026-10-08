import type { ChatResponse, Product } from "./types";
import type { AuthSession, AuthUser } from "./auth";
import type { StoredChatMessage } from "./types";

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok) {
    const message = response.status === 404 ? "Product not found" : "The store is temporarily unavailable";
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const getProducts = (signal?: AbortSignal) => request<Product[]>("/api/products", signal);

export const getProduct = (id: string, signal?: AbortSignal) =>
  request<Product>(`/api/products/${encodeURIComponent(id)}`, signal);

interface ApiErrorBody { detail?: string | Array<{ msg: string }> }

export class ApiError extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}

async function post<T>(path: string, body: unknown, token?: string | null): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { method: "POST", headers, body: JSON.stringify(body) });
  if (!response.ok) {
    let error: ApiErrorBody = {};
    try { error = await response.json() as ApiErrorBody; } catch { /* Use fallback below. */ }
    const detail = Array.isArray(error.detail) ? error.detail[0]?.msg : error.detail;
    throw new ApiError(detail?.replace(/^Value error, /, "") || "Something went wrong. Please try again.", response.status);
  }
  return response.json() as Promise<T>;
}

export const registerUser = (payload: { first_name: string; last_name: string; email: string; password: string; password_confirmation: string }) =>
  post<AuthUser>("/api/auth/register", payload);

export const loginUser = (email: string, password: string) => post<AuthSession>("/api/auth/login", { email, password });

export const sendChatMessage = (
  message: string,
  history: Array<{ role: "user" | "assistant"; content: string }>,
  page: { path: string; product_id: string | null },
  token?: string | null,
) => post<ChatResponse>("/api/chat", { message, history, page }, token);

export async function getChatHistory(token: string): Promise<StoredChatMessage[]> {
  const response = await fetch("/api/chat/history", { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new ApiError("Conversation history could not be loaded", response.status);
  return response.json() as Promise<StoredChatMessage[]>;
}
