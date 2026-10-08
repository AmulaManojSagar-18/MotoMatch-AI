// Types mirroring the backend API contract (Phases 1-3).

/** Recommendation payload returned by POST /chat when a bike is chosen. */
export interface Recommendation {
  bike_id: number;
  bike_name: string;
  score: number;
  matching_factors: string[];
}

/** Response body of POST /chat. */
export interface ChatResponse {
  conversation_id: string;
  message: string;
  recommendation: Recommendation | null;
}

/** Full factual bike record returned by GET /bikes/{id}. */
export interface Bike {
  id: number;
  brand: string;
  model: string;
  category: string;
  price: number | null;
  engine_cc: number | null;
  power_ps: number | null;
  torque_nm: number | null;
  weight_kg: number | null;
  seat_height_mm: number | null;
  fuel_capacity_l: number | null;
  ground_clearance_mm: number | null;
  transmission: string | null;
  abs_type: string | null;
  mileage: number | null;
  model_3d_url: string | null;
}

/** A single message rendered in the chat window. */
export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  /** Attached when the assistant turn produced a recommendation. */
  recommendation?: Recommendation;
  /** Factual specs fetched for the recommended bike (if available). */
  bike?: Bike;
  /** Marks a user-facing error turn (rendered distinctly). */
  isError?: boolean;
}
