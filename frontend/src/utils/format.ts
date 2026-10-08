// Small presentation helpers (formatting only - no business logic).

/** Format an INR integer price as lakhs (or plain rupees under 1 lakh). */
export function formatPrice(price: number | null): string | null {
  if (price == null) return null;
  if (price >= 100000) {
    return `₹${(price / 100000).toFixed(2)} Lakh`;
  }
  return `₹${price.toLocaleString("en-IN")}`;
}

const FACTOR_LABELS: Record<string, string> = {
  fits_budget: "Fits your budget",
  high_city_suitability: "Great for city riding",
  good_for_highway_and_weekend_trips: "Highway & weekend ready",
  good_for_adventure_riding: "Adventure capable",
  comfort_priority_match: "Comfortable ride",
  good_mileage: "Great mileage",
  strong_performance: "Strong performance",
};

/** Turn an engine matching-factor key into a readable chip label. */
export function humanizeFactor(factor: string): string {
  if (FACTOR_LABELS[factor]) return FACTOR_LABELS[factor];
  return factor
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
