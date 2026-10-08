// Maps backend bike id -> local PNG under /public/bikes.
// Using the numeric id (stable) rather than the display name (brittle).
// Ids follow the seeded catalog order in PostgreSQL (1..10).

export const bikeImages: Record<number, string> = {
  1: "/bikes/hero-splendor-plus.png",
  2: "/bikes/hero-xpulse-200-4v.png",
  3: "/bikes/tvs-ronin-225.png",
  4: "/bikes/yamaha-r15-v4.png",
  5: "/bikes/royal-enfield-hunter-350.png",
  6: "/bikes/honda-cb350.png",
  7: "/bikes/triumph-speed-400.png",
  8: "/bikes/bajaj-pulsar-ns400z.png",
  9: "/bikes/royal-enfield-guerrilla-450.png",
  10: "/bikes/royal-enfield-continental-gt-650.png",
};

/** Return the image path for a bike id, or null if we have none. */
export function getBikeImage(bikeId: number): string | null {
  return bikeImages[bikeId] ?? null;
}
