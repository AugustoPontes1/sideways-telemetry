import { Component, Suspense, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { Box3, Vector3 } from 'three';
import type { Group } from 'three';
import type { MutableRefObject, ReactNode } from 'react';
import type { CarVisual, TelemetrySample } from '../../lib/types';
import { radiansToDegrees } from '../../lib/telemetry';

interface CarProfile {
  width: number;
  length: number;
  height: number;
  roofWidth: number;
  roofLength: number;
  color: string;
  accent: string;
  spoiler: boolean;
}

function colorForCar(carName: string): { color: string; accent: string } {
  let hash = 0;
  for (const character of carName) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  const hue = hash % 360;
  return { color: `hsl(${hue} 36% 78%)`, accent: `hsl(${(hue + 150) % 360} 68% 55%)` };
}

function profileForCar(carName = '', carVisual?: CarVisual | null): CarProfile {
  const name = `${carName} ${carVisual?.id || ''} ${carVisual?.display_name || ''} ${carVisual?.brand || ''}`.toLowerCase();
  const modColors = colorForCar(carVisual?.id || carName);
  if (/(truck|pickup|van|suv|wagon|utility)/.test(name)) {
    return { width: 2.05, length: 5.1, height: 1.05, roofWidth: 1.7, roofLength: 2.35, ...modColors, spoiler: false };
  }
  if (/(gt3|gt4|gtr|race|racing|tcr|dtm|touring|cup)/.test(name)) {
    return { width: 1.96, length: 4.65, height: .84, roofWidth: 1.5, roofLength: 2.1, ...modColors, spoiler: true };
  }
  if (/(drift|silvia|s13|s14|s15|skyline|rx-7|supra|jzx|ae86|180sx)/.test(name)) {
    return { width: 1.88, length: 4.35, height: .82, roofWidth: 1.5, roofLength: 2.05, color: modColors.color, accent: modColors.accent, spoiler: true };
  }
  if (/(miata|mx-5|roadster|s2000|gt86|brz)/.test(name)) {
    return { width: 1.75, length: 3.9, height: .72, roofWidth: 1.35, roofLength: 1.65, ...modColors, spoiler: false };
  }
  if (/(formula|f1|openwheel|lotus)/.test(name)) {
    return { width: 1.82, length: 4.7, height: .62, roofWidth: .85, roofLength: 1.25, ...modColors, spoiler: true };
  }
  return { width: 1.9, length: 4.3, height: .8, roofWidth: 1.48, roofLength: 2.05, ...modColors, spoiler: true };
}

function externalModelUrl(carVisual?: CarVisual | null): string | null {
  const baseUrl = (import.meta.env.VITE_CAR_MODELS_BASE_URL || '/car-models').trim().replace(/\/+$/, '');
  if (!carVisual?.asset_key) return null;
  const skin = carVisual.skin_id?.trim();
  return `${baseUrl}/${encodeURIComponent(carVisual.asset_key)}.glb${skin ? `?skin=${encodeURIComponent(skin)}` : ''}`;
}

function ExternalCarModel({ url, targetLength }: { url: string; targetLength: number }) {
  const { scene } = useGLTF(url);
  const model = useMemo(() => {
    const clone = scene.clone(true);
    const sourceBounds = new Box3().setFromObject(clone);
    const sourceSize = sourceBounds.getSize(new Vector3());
    const horizontalSize = Math.max(sourceSize.x, sourceSize.z);
    if (horizontalSize > 0) clone.scale.setScalar(targetLength / horizontalSize);
    const bounds = new Box3().setFromObject(clone);
    const center = bounds.getCenter(new Vector3());
    clone.position.x -= center.x;
    clone.position.y -= bounds.min.y;
    clone.position.z -= center.z;
    clone.traverse((object) => {
      if ('isMesh' in object && object.isMesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    return clone;
  }, [scene, targetLength]);
  return <primitive object={model} />;
}

class ModelErrorBoundary extends Component<{ fallback: ReactNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

function ProceduralCar({ profile, wheelRefs }: { profile: CarProfile; wheelRefs: MutableRefObject<Array<Group | null>> }) {
  const wheelZ = profile.length * .31;
  return <>
    <mesh castShadow position={[0, .3, 0]}>
      <boxGeometry args={[profile.width, .48, profile.length]}/>
      <meshStandardMaterial color={profile.color} metalness={.38} roughness={.3}/>
    </mesh>
    <mesh castShadow position={[0, .56, -profile.length * .31]}>
      <boxGeometry args={[profile.width * .88, .16, profile.length * .27]}/>
      <meshStandardMaterial color={profile.color} metalness={.34} roughness={.32}/>
    </mesh>
    <mesh castShadow position={[0, .58, profile.length * .31]}>
      <boxGeometry args={[profile.width * .82, .15, profile.length * .2]}/>
      <meshStandardMaterial color={profile.color} metalness={.34} roughness={.32}/>
    </mesh>
    <mesh castShadow position={[0, .86, .04]}>
      <boxGeometry args={[profile.roofWidth, profile.height, profile.roofLength]}/>
      <meshStandardMaterial color="#263e53" metalness={.4} roughness={.24}/>
    </mesh>
    <mesh position={[0, .91, -.42]}>
      <boxGeometry args={[profile.roofWidth * .92, .025, profile.roofLength * .31]}/>
      <meshStandardMaterial color="#89b7c9" metalness={.1} roughness={.18} transparent opacity={.75}/>
    </mesh>
    <mesh position={[0, .91, .45]}>
      <boxGeometry args={[profile.roofWidth * .92, .025, profile.roofLength * .28]}/>
      <meshStandardMaterial color="#89b7c9" metalness={.1} roughness={.18} transparent opacity={.7}/>
    </mesh>
    <mesh castShadow position={[0, .45, -profile.length / 2 - .04]}>
      <boxGeometry args={[profile.width * .82, .13, .12]}/>
      <meshStandardMaterial color={profile.accent} emissive={profile.accent} emissiveIntensity={.28}/>
    </mesh>
    <mesh castShadow position={[0, .43, profile.length / 2 + .04]}>
      <boxGeometry args={[profile.width * .84, .13, .12]}/>
      <meshStandardMaterial color="#d74d58" emissive="#6e1826" emissiveIntensity={.35}/>
    </mesh>
    {[-1, 1].map((side) => <mesh key={`mirror-${side}`} castShadow position={[side * (profile.roofWidth / 2 + .1), .8, -.32]}>
      <boxGeometry args={[.12, .1, .2]}/>
      <meshStandardMaterial color={profile.accent} metalness={.4} roughness={.3}/>
    </mesh>)}
    {profile.spoiler && <group position={[0, .72, profile.length * .45]}>
      <mesh castShadow position={[0, .11, 0]}>
        <boxGeometry args={[profile.width * .78, .08, .1]}/>
        <meshStandardMaterial color={profile.accent} metalness={.3} roughness={.3}/>
      </mesh>
      {[-1, 1].map((side) => <mesh key={`wing-${side}`} position={[side * profile.width * .29, .03, 0]}>
        <boxGeometry args={[.07, .18, .08]}/>
        <meshStandardMaterial color={profile.accent}/>
      </mesh>)}
    </group>}
    {[-1, 1].flatMap((side, sideIndex) => [-1, 1].map((front, frontIndex) => {
      const wheelIndex = sideIndex * 2 + frontIndex;
      return <group key={`${side}-${front}`} ref={(node) => { wheelRefs.current[wheelIndex] = node; }} position={[side * (profile.width / 2 + .08), .17, front * wheelZ]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[.4, .4, .3, 18]}/>
          <meshStandardMaterial color="#0b1118" roughness={.88}/>
        </mesh>
        <mesh rotation={[0, 0, Math.PI / 2]} position={[side * .16, 0, 0]}>
          <cylinderGeometry args={[.18, .18, .02, 12]}/>
          <meshStandardMaterial color="#8997a6" metalness={.75} roughness={.24}/>
        </mesh>
      </group>;
    }))}
    <mesh position={[0, 1.42, 0]}>
      <boxGeometry args={[.04, .04, .55]}/>
      <meshBasicMaterial color="#ffa45d"/>
    </mesh>
  </>;
}

export function CarModel({ sample, origin, carName, carVisual }: {
  sample: TelemetrySample;
  origin: [number, number, number];
  carName?: string;
  carVisual?: CarVisual | null;
}) {
  const profile = profileForCar(carName, carVisual);
  const position: [number, number, number] = [
    sample.position_world_m[0] - origin[0],
    sample.position_world_m[1] - origin[1] + .55,
    sample.position_world_m[2] - origin[2],
  ];
  const yaw = sample.heading_rad;
  const wheelSteer = Math.max(-.45, Math.min(.45, sample.steer_angle_rad * .25));
  const groupRef = useRef<Group>(null);
  const wheelRefs = useRef<Array<Group | null>>([]);
  const initialPosition = useRef(position);
  const initialRotation = useRef<[number, number, number]>([0, yaw, 0]);
  const target = useRef({ position, yaw, wheelSteer });
  target.current = { position, yaw, wheelSteer };
  const modelUrl = externalModelUrl(carVisual);
  const proceduralFallback = <ProceduralCar profile={profile} wheelRefs={wheelRefs}/>;

  useFrame(() => {
    const group = groupRef.current;
    if (!group) return;
    group.position.set(...target.current.position);
    group.rotation.y = target.current.yaw;
    wheelRefs.current.forEach((wheel, wheelIndex) => {
      if (!wheel) return;
      wheel.rotation.y = wheelIndex % 2 === 0 ? target.current.wheelSteer : 0;
    });
  });

  return <group ref={groupRef} position={initialPosition.current} rotation={initialRotation.current}>
    {modelUrl ? <ModelErrorBoundary key={modelUrl} fallback={proceduralFallback}>
      <Suspense fallback={proceduralFallback}>
        <ExternalCarModel url={modelUrl} targetLength={profile.length}/>
      </Suspense>
    </ModelErrorBoundary> : proceduralFallback}
    <group userData={{ carName: carName || 'unknown', carId: carVisual?.id || 'unknown', heading_deg: radiansToDegrees(yaw) }}/>
  </group>;
}
