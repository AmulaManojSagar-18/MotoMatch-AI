import type { Bike } from "../../types";
import "./BikeSpecs.css";

interface Props {
  bike: Bike;
}

interface Spec {
  label: string;
  value: string;
}

/** Compact grid of key factual specs. Only renders fields that exist. */
export default function BikeSpecs({ bike }: Props) {
  const specs: Spec[] = [];

  if (bike.engine_cc != null) specs.push({ label: "Engine", value: `${bike.engine_cc} cc` });
  if (bike.power_ps != null) specs.push({ label: "Power", value: `${bike.power_ps} PS` });
  if (bike.torque_nm != null) specs.push({ label: "Torque", value: `${bike.torque_nm} Nm` });
  if (bike.mileage != null) specs.push({ label: "Mileage", value: `${bike.mileage} km/l` });
  if (bike.weight_kg != null) specs.push({ label: "Weight", value: `${bike.weight_kg} kg` });
  if (bike.seat_height_mm != null)
    specs.push({ label: "Seat Height", value: `${bike.seat_height_mm} mm` });
  if (bike.abs_type) specs.push({ label: "ABS", value: bike.abs_type });
  if (bike.transmission) specs.push({ label: "Gearbox", value: bike.transmission });

  if (specs.length === 0) return null;

  return (
    <div className="bike-specs">
      {specs.map((spec) => (
        <div className="bike-specs__item" key={spec.label}>
          <span className="bike-specs__value">{spec.value}</span>
          <span className="bike-specs__label">{spec.label}</span>
        </div>
      ))}
    </div>
  );
}
