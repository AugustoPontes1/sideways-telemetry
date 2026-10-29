import { Component, Suspense, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import { Box3, Vector3 } from 'three';
import type { Group, Object3D } from 'three';
import type { MutableRefObject, ReactNode } from 'react';
import type { CarVisual, TelemetrySample } from '../../lib/types';
import { radiansToDegrees } from '../../lib/telemetry';
import { acHeadingToSceneYaw } from '../../lib/trackMap';

interface CarProfile {
  width: number;
  length: number;
  height: number;
  roofWidth: number;
  roofLength: number;
  color: string;
  accent: string;
  spoiler: boolean;
  variant?: 'jimny';
}

function colorForCar(carName: string): { color: string; accent: string } {
  let hash = 0;
  for (const character of carName) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  const hue = hash % 360;
  return { color: `hsl(${hue} 36% 78%)`, accent: `hsl(${(hue + 150) % 360} 68% 55%)` };
}

function carColors(carName: string, carVisual?: CarVisual | null): { color: string; accent: string } {
  const fallback = colorForCar(carVisual?.id || carName);
  const skinColor = carVisual?.color_hex?.trim();
  return skinColor && /^#[0-9a-f]{6}$/i.test(skinColor)
    ? { ...fallback, color: skinColor }
    : fallback;
}

function profileForCar(carName = '', carVisual?: CarVisual | null): CarProfile {
  const name = `${carName} ${carVisual?.id || ''} ${carVisual?.display_name || ''} ${carVisual?.brand || ''}`.toLowerCase();
  const modColors = carColors(carName, carVisual);
  if (/(jimny|sierra|4x4|offroad|land cruiser|defender)/.test(name)) {
    return { width: 1.85, length: 3.7, height: 1.12, roofWidth: 1.62, roofLength: 2.15, ...modColors, spoiler: false, variant: 'jimny' };
  }
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

type WheelRotation = [number, number, number];
type WheelRefs = MutableRefObject<Array<Object3D | null>>;

function isWheelNode(object: Object3D): boolean {
  const name = object.name.toLowerCase();
  if (!/(wheel|tyre|tire|pneu|ruota)/.test(name) || /(steer|volante|handwheel)/.test(name)) return false;
  const parentName = object.parent?.name.toLowerCase() || '';
  return !parentName || !/(wheel|tyre|tire|pneu|ruota)/.test(parentName) || /^(wheels?|tyres?|tires?|pneus?|ruote?)$/.test(parentName);
}

function hasWheelLikeGeometry(object: Object3D): boolean {
  if (!('isMesh' in object) || !object.isMesh || !('geometry' in object)) return false;
  const geometry = object.geometry as { boundingBox?: { min: Vector3; max: Vector3 }; computeBoundingBox?: () => void };
  if (!geometry.boundingBox && geometry.computeBoundingBox) geometry.computeBoundingBox();
  if (!geometry.boundingBox) return false;
  const size = new Vector3().subVectors(geometry.boundingBox.max, geometry.boundingBox.min).toArray().map(Math.abs).sort((a, b) => a - b);
  return size[0] > 0.02 && size[2] / size[0] < 4.5 && size[2] / size[1] < 2.6;
}

function ExternalCarModel({
  url, targetLength, wheelRefs, frontWheelRefs, wheelBaseRotations,
}: {
  url: string;
  targetLength: number;
  wheelRefs: WheelRefs;
  frontWheelRefs: WheelRefs;
  wheelBaseRotations: MutableRefObject<WeakMap<Object3D, WheelRotation>>;
}) {
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
    clone.updateMatrixWorld(true);
    return clone;
  }, [scene, targetLength]);

  useLayoutEffect(() => {
    const namedWheels: Object3D[] = [];
    const geometricWheels: Object3D[] = [];
    model.traverse((object) => {
      if ('isMesh' in object && object.isMesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
      if (isWheelNode(object)) namedWheels.push(object);
      if (hasWheelLikeGeometry(object)) {
        const position = object.getWorldPosition(new Vector3());
        if (position.y < 1.1 && Math.abs(position.x) > .25) geometricWheels.push(object);
      }
    });
    const detectedWheels = [...new Set(namedWheels.length >= 4 ? namedWheels : [...namedWheels, ...geometricWheels])];
    const frontWheels = detectedWheels.filter((wheel) => wheel.getWorldPosition(new Vector3()).z < 0);
    const steeringWheels = frontWheels.length >= 2 ? frontWheels : detectedWheels.slice(0, 2);
    wheelRefs.current = detectedWheels;
    frontWheelRefs.current = detectedWheels.map((wheel) => steeringWheels.includes(wheel) ? wheel : null);
    detectedWheels.forEach((wheel) => {
      wheelBaseRotations.current.set(wheel, [wheel.rotation.x, wheel.rotation.y, wheel.rotation.z]);
    });
    return () => {
      if (wheelRefs.current.some((wheel) => wheel && detectedWheels.includes(wheel))) wheelRefs.current = [];
      if (frontWheelRefs.current.some((wheel) => wheel && detectedWheels.includes(wheel))) frontWheelRefs.current = [];
    };
  }, [model, wheelBaseRotations, wheelRefs, frontWheelRefs]);
  return <primitive object={model} />;
}

class ModelErrorBoundary extends Component<{ fallback: ReactNode; children: ReactNode; onFailure?: () => void }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch() {
    this.props.onFailure?.();
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

function ProceduralCar({ profile, wheelRefs, frontWheelRefs }: { profile: CarProfile; wheelRefs: WheelRefs; frontWheelRefs: WheelRefs }) {
  const wheelZ = profile.length * .31;
  const isJimny = profile.variant === 'jimny';
  return <group position={[0, .23, 0]}>
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
    {isJimny && <>
      {[-1, 1].map((side) => <mesh key={`jimny-window-${side}`} position={[side * (profile.roofWidth / 2 + .015), .91, -.06]}>
        <boxGeometry args={[.025, .34, 1.34]}/>
        <meshStandardMaterial color="#36566d" metalness={.15} roughness={.22} transparent opacity={.86}/>
      </mesh>)}
      <mesh castShadow position={[0, .43, -profile.length / 2 - .1]}>
        <boxGeometry args={[profile.width * .9, .16, .16]}/>
        <meshStandardMaterial color="#151d25" metalness={.25} roughness={.65}/>
      </mesh>
      <mesh position={[0, .51, -profile.length / 2 - .185]}>
        <boxGeometry args={[.58, .14, .025]}/>
        <meshStandardMaterial color="#080c11" roughness={.8}/>
      </mesh>
      {[-1, 1].map((side) => <mesh key={`jimny-headlight-${side}`} position={[side * .54, .53, -profile.length / 2 - .19]}>
        <boxGeometry args={[.22, .16, .035]}/>
        <meshStandardMaterial color="#f5d99d" emissive="#a77437" emissiveIntensity={.42}/>
      </mesh>)}
      <mesh castShadow rotation={[Math.PI / 2, 0, 0]} position={[0, .72, profile.length / 2 + .12]}>
        <cylinderGeometry args={[.34, .34, .14, 20]}/>
        <meshStandardMaterial color="#0b1118" roughness={.88}/>
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, .72, profile.length / 2 + .205]}>
        <cylinderGeometry args={[.14, .14, .025, 12]}/>
        <meshStandardMaterial color="#8997a6" metalness={.75} roughness={.24}/>
      </mesh>
    </>}
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
      return <group key={`${side}-${front}`} ref={(node) => {
        if (node) {
          node.userData.proceduralWheel = true;
          wheelRefs.current[wheelIndex] = node;
          frontWheelRefs.current[wheelIndex] = front === -1 ? node : null;
        } else if (wheelRefs.current[wheelIndex]?.userData.proceduralWheel) {
          wheelRefs.current[wheelIndex] = null;
          frontWheelRefs.current[wheelIndex] = null;
        }
      }} position={[side * (profile.width / 2 + .08), .17, front * wheelZ]}>
        <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[.4, .4, .3, 18]}/>
          <meshStandardMaterial color="#0b1118" roughness={.88}/>
        </mesh>
        <mesh rotation={[0, 0, Math.PI / 2]} position={[side * .16, 0, 0]}>
          <cylinderGeometry args={[.18, .18, .02, 12]}/>
          <meshStandardMaterial color="#8997a6" metalness={.75} roughness={.24}/>
        </mesh>
        <mesh position={[side * .18, 0, 0]}>
          <boxGeometry args={[.025, .27, .045]}/>
          <meshStandardMaterial color="#d3e6ed" metalness={.7} roughness={.2}/>
        </mesh>
        <mesh position={[side * .18, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <boxGeometry args={[.025, .27, .045]}/>
          <meshStandardMaterial color="#d3e6ed" metalness={.7} roughness={.2}/>
        </mesh>
      </group>;
    }))}
    <mesh position={[0, 1.42, 0]}>
      <boxGeometry args={[.04, .04, .55]}/>
      <meshBasicMaterial color="#ffa45d"/>
    </mesh>
  </group>;
}

function dampAngle(current: number, target: number, amount: number): number {
  const delta = Math.atan2(Math.sin(target - current), Math.cos(target - current));
  return current + delta * amount;
}

export function CarModel({ sample, origin, carName, carVisual, onModelFallback }: {
  sample: TelemetrySample;
  origin: [number, number, number];
  carName?: string;
  carVisual?: CarVisual | null;
  onModelFallback?: (active: boolean) => void;
}) {
  const profile = profileForCar(carName, carVisual);
  const position: [number, number, number] = [
    sample.position_world_m[0] - origin[0],
    sample.position_world_m[1] - origin[1] + .04,
    sample.position_world_m[2] - origin[2],
  ];
  const yaw = acHeadingToSceneYaw(sample.heading_rad);
  const pitch = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, sample.pitch_rad ?? 0));
  const roll = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, sample.roll_rad ?? 0));
  const wheelSteer = Math.max(-.62, Math.min(.62, sample.steer_angle_rad * .55));
  const groupRef = useRef<Group>(null);
  const wheelRefs = useRef<Array<Object3D | null>>([]);
  const frontWheelRefs = useRef<Array<Object3D | null>>([]);
  const wheelBaseRotations = useRef(new WeakMap<Object3D, WheelRotation>());
  const wheelSpin = useRef(0);
  const [modelFailed, setModelFailed] = useState(false);
  const initialPosition = useRef(position);
  const initialRotation = useRef<[number, number, number]>([pitch, yaw, roll]);
  const target = useRef({ position, yaw, pitch, roll, wheelSteer, wheelSpinRate: 0 });
  const wheelRadius = Math.max(.28, profile.height * .5);
  const speedMps = Math.abs(sample.speed_mps) > .02 ? sample.speed_mps : sample.speed_kmh / 3.6;
  target.current = { position, yaw, pitch, roll, wheelSteer, wheelSpinRate: speedMps / wheelRadius };
  const modelUrl = externalModelUrl(carVisual);
  const proceduralFallback = <ProceduralCar profile={profile} wheelRefs={wheelRefs} frontWheelRefs={frontWheelRefs}/>;

  useEffect(() => {
    setModelFailed(false);
  }, [modelUrl]);

  useEffect(() => {
    onModelFallback?.(Boolean(!modelUrl || modelFailed));
    return () => onModelFallback?.(false);
  }, [modelFailed, modelUrl, onModelFallback]);

  useFrame((_state, delta) => {
    const group = groupRef.current;
    if (!group) return;
    group.rotation.order = 'YXZ';
    const movementAmount = 1 - Math.exp(-delta * 24);
    group.position.x += (target.current.position[0] - group.position.x) * movementAmount;
    group.position.y += (target.current.position[1] - group.position.y) * movementAmount;
    group.position.z += (target.current.position[2] - group.position.z) * movementAmount;
    group.rotation.x += (target.current.pitch - group.rotation.x) * movementAmount;
    group.rotation.y = dampAngle(group.rotation.y, target.current.yaw, movementAmount);
    group.rotation.z += (target.current.roll - group.rotation.z) * movementAmount;
    wheelSpin.current -= target.current.wheelSpinRate * delta;
    wheelRefs.current.forEach((wheel) => {
      if (!wheel) return;
      const base = wheelBaseRotations.current.get(wheel) ?? [wheel.rotation.x, wheel.rotation.y, wheel.rotation.z];
      wheelBaseRotations.current.set(wheel, base);
      wheel.rotation.order = 'YXZ';
      wheel.rotation.x = base[0] + wheelSpin.current;
      wheel.rotation.y = base[1] + (frontWheelRefs.current.includes(wheel) ? target.current.wheelSteer : 0);
      wheel.rotation.z = base[2];
    });
  });

  return <group ref={groupRef} position={initialPosition.current} rotation={initialRotation.current}>
    {modelUrl ? <ModelErrorBoundary key={modelUrl} fallback={proceduralFallback} onFailure={() => setModelFailed(true)}>
      <Suspense fallback={proceduralFallback}>
        <ExternalCarModel
          url={modelUrl}
          targetLength={profile.length}
          wheelRefs={wheelRefs}
          frontWheelRefs={frontWheelRefs}
          wheelBaseRotations={wheelBaseRotations}
        />
      </Suspense>
    </ModelErrorBoundary> : proceduralFallback}
    <group userData={{ carName: carName || 'unknown', carId: carVisual?.id || 'unknown', heading_deg: radiansToDegrees(yaw) }}/>
  </group>;
}
