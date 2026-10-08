// Thin API client for the MotoMatch backend. All network access lives here so
// components stay presentation-only and the base URL is configured in one place.

import { API_BASE_URL } from "../config";
import type { Bike, ChatResponse } from "../types";

/** Raised for any failed/invalid backend interaction (used for friendly UI messages). */
export class ApiError extends Error {}

const REQUEST_TIMEOUT_MS = 120_000; // LLM turns can take a while on local models.

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("The request timed out. Please try again.");
    }
    throw new ApiError(
      "Could not reach MotoMatch. Make sure the backend is running.",
    );
  }
  clearTimeout(timeout);

  if (!response.ok) {
    // Surface a clean message; never leak raw server internals to the user.
    let detail = "";
    try {
      const data = await response.json();
      detail = typeof data?.detail === "string" ? data.detail : "";
    } catch {
      /* ignore parse errors */
    }
    if (response.status === 502) {
      throw new ApiError(
        "The AI service is currently unavailable. Please try again shortly.",
      );
    }
    throw new ApiError(detail || `Request failed (${response.status}).`);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("Received an invalid response from the server.");
  }
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new ApiError("Could not reach MotoMatch backend.");
  }
  if (!response.ok) {
    throw new ApiError(`Request failed (${response.status}).`);
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("Received an invalid response from the server.");
  }
}

/** Send a chat message. Pass the existing conversation id to continue a chat. */
export function sendChatMessage(
  message: string,
  conversationId: string | null,
): Promise<ChatResponse> {
  return postJson<ChatResponse>("/chat", {
    message,
    conversation_id: conversationId,
  });
}

/** Fetch the full factual specs for a bike by id. */
export function getBike(bikeId: number): Promise<Bike> {
  return getJson<Bike>(`/bikes/${bikeId}`);
}
