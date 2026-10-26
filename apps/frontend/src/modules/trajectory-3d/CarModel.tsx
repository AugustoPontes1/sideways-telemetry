import { useMemo } from 'react';
import type { TelemetrySample } from '../../lib/types';
import { radiansToDegrees } from '../../lib/telemetry';

/** Educational geometric model; it does NOT reproduce the mod's actual bodywork or wheels. */
export function CarModel({ sample, origin }: { sample: TelemetrySample; origin: [number, number, number] }) {
  const position: [number, number, number] = [
    sample.position_world_m[0] - origin[0],
    sample.position_world_m[1] - origin[1] + .55,
    sample.position_world_m[2] - origin[2],
  ];
  const yaw = sample.heading_rad;
  const wheelSteer = useMemo(() => Math.max(-.45, Math.min(.45, sample.steer_angle_rad * .25)), [sample.steer_angle_rad]);
  return <group position={position} rotation={[0, yaw, 0]}>
    <mesh castShadow position={[0, .36, 0]}>
      <boxGeometry args={[1.85, .52, 4.3]}/>
      <meshStandardMaterial color="#d9e8f5" metalness={.35} roughness={.32}/>
    </mesh>
    <mesh castShadow position={[0, .89, -.3]}>
      <boxGeometry args={[1.57, .65, 2.13]}/>
      <meshStandardMaterial color="#2c4f62" metalness={.5} roughness={.27}/>
    </mesh>
    <mesh castShadow position={[0, .52, -1.94]}>
      <boxGeometry args={[1.3, .12, .15]}/>
      <meshStandardMaterial color="#0bbda7" emissive="#036d67" emissiveIntensity={.5}/>
    </mesh>
    {[-1, 1].flatMap((side) => [-1.35, 1.35].map((front) =>
      <group key={`${side}-${front}`} position={[side * 1.03, .14, front]}
        rotation={[0, front < 0 ? wheelSteer : 0, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[.43, .43, .31, 16]}/>
          <meshStandardMaterial color="#10151e" roughness={.9}/>
        </mesh>
      </group>))}
    <mesh position={[0, 1.55, 0]}>
      <boxGeometry args={[.05, .05, .7]}/>
      <meshBasicMaterial color="#ffa45d"/>
    </mesh>
    <group position={[0, 1.9, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <coneGeometry args={[.34, 1.1, 12]}/>
        <meshBasicMaterial color="#e4aa5d"/>
      </mesh>
    </group>
    <group userData={{ heading_deg_unvalidated: radiansToDegrees(yaw) }}/>
  </group>;
}
