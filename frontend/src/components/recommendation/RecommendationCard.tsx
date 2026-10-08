import type { Bike, Recommendation } from "../../types";
import { formatPrice, humanizeFactor } from "../../utils/format";
import BikeImage from "./BikeImage";
import BikeSpecs from "./BikeSpecs";
import "./RecommendationCard.css";

interface Props {
  recommendation: Recommendation;
  /** Full factual specs fetched from GET /bikes/{id} (optional). */
  bike?: Bike;
  /** The AI's grounded explanation (the chat message for this turn). */
  explanation: string;
}

/**
 * Polished recommendation card. The chosen bike always comes from the backend;
 * this component only presents it. Factual fields are shown only when present.
 */
export default function RecommendationCard({ recommendation, bike, explanation }: Props) {
  const price = bike ? formatPrice(bike.price) : null;

  return (
    <article className="rec-card" aria-label="Recommended bike">
      <div className="rec-card__eyebrow">
        <span aria-hidden="true">★</span> Your recommended bike
      </div>

      <BikeImage bikeId={recommendation.bike_id} bikeName={recommendation.bike_name} />

      <div className="rec-card__body">
        <div>
          <h2 className="rec-card__title">{recommendation.bike_name}</h2>
          {bike?.category && <p className="rec-card__subtitle">{bike.category}</p>}
          <div>
            {price && <span className="rec-card__price">{price}</span>}
            <span className="rec-card__score">
              {Math.round(recommendation.score)}% match
            </span>
          </div>
        </div>

        {bike && <BikeSpecs bike={bike} />}

        <div>
          <h3 className="rec-card__why-heading">Why this bike?</h3>
          <p className="rec-card__why-text">{explanation}</p>

          {recommendation.matching_factors.length > 0 && (
            <ul className="rec-card__factors">
              {recommendation.matching_factors.map((factor) => (
                <li className="rec-card__factor" key={factor}>
                  {humanizeFactor(factor)}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </article>
  );
}
