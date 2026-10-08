import { useState } from "react";
import { getBikeImage } from "../../data/bikeImages";
import "./BikeImage.css";

interface Props {
  bikeId: number;
  bikeName: string;
}

/** Shows the bike PNG; falls back to a clean placeholder if missing/broken. */
export default function BikeImage({ bikeId, bikeName }: Props) {
  const src = getBikeImage(bikeId);
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div className="bike-image bike-image--fallback" role="img" aria-label={bikeName}>
        <span className="bike-image__emoji" aria-hidden="true">
          🏍️
        </span>
        <span className="bike-image__fallback-name">{bikeName}</span>
      </div>
    );
  }

  return (
    <div className="bike-image">
      <img
        src={src}
        alt={bikeName}
        loading="lazy"
        onError={() => setFailed(true)}
      />
    </div>
  );
}
