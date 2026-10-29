import { useCallback, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useLoader, useThree } from '@react-three/fiber';
import { Grid, Line, OrbitControls, PerspectiveCamera } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { BufferGeometry, DoubleSide, Float32BufferAttribute, SRGBColorSpace, TextureLoader, Vector3 } from 'three';
import type { CarVisual, TelemetrySample, TrackMap, Vec3 } from '../../lib/types';
import { downsample } from '../../lib/telemetry';
import { mapPlaneTransform } from '../../lib/trackMap';
import { TrackMiniMap } from '../../components/TrackMiniMap';
import { CarModel } from './CarModel';

function TrackSurface({ trackMap, origin }: { trackMap?: TrackMap | null; origin: Vec3 }) {
  const imageUrl = trackMap?.image_url;
  const config = trackMap?.map_config;
  const trackPoints = useMemo(() => downsample(trackMap?.points || [], 1600).map((point) => [
    point[0] - origin[0],
    point[1] - origin[1],
    point[2] - origin[2],
  ] as Vec3), [origin, trackMap]);
  const trackWidth = useMemo(() => {
    if (trackPoints.length < 2) return 8;
    const spanX = Math.max(...trackPoints.map((point) => point[0])) - Math.min(...trackPoints.map((point) => point[0]));
    const spanZ = Math.max(...trackPoints.map((point) => point[2])) - Math.min(...trackPoints.map((point) => point[2]));
    return Math.max(7, Math.min(14, Math.max(spanX, spanZ) / 80));
  }, [trackPoints]);
  const ribbonGeometry = useMemo(() => createTrackRibbon(trackPoints, trackWidth), [trackPoints, trackWidth]);
  const surfaceY = useMemo(() => trackPoints.length
    ? Math.min(...trackPoints.map((point) => point[1])) - .8
    : -.8, [trackPoints]);
  return <>
    {imageUrl && config && <TrackSurfaceMesh imageUrl={imageUrl} config={config} origin={origin} surfaceY={surfaceY}/>}
    {trackPoints.length >= 2 && <mesh geometry={ribbonGeometry} receiveShadow>
      <meshStandardMaterial color="#263f4d" roughness={.96} metalness={0} side={DoubleSide} transparent opacity={.9}/>
    </mesh>}
    {trackPoints.length >= 2 && <Line points={trackPoints} color="#547087" lineWidth={1.5} transparent opacity={.65}/>}
  </>;
}

function createTrackRibbon(points: Vec3[], width: number): BufferGeometry {
  const geometry = new BufferGeometry();
  if (points.length < 2) return geometry;
  const closes = Math.hypot(points[0][0] - points.at(-1)![0], points[0][2] - points.at(-1)![2]) < width;
  const usable = closes ? points.slice(0, -1) : points;
  if (usable.length < 2) return geometry;
  const positions: number[] = [];
  const indices: number[] = [];
  const halfWidth = width / 2;
  const end = closes ? usable.length : usable.length - 1;
  for (let index = 0; index < usable.length; index += 1) {
    const point = usable[index];
    const previous = usable[index === 0 ? (closes ? usable.length - 1 : 0) : index - 1];
    const next = usable[index === usable.length - 1 ? (closes ? 0 : usable.length - 1) : index + 1];
    const tangentX = next[0] - previous[0];
    const tangentZ = next[2] - previous[2];
    const tangentLength = Math.hypot(tangentX, tangentZ) || 1;
    const normalX = -tangentZ / tangentLength;
    const normalZ = tangentX / tangentLength;
    positions.push(
      point[0] + normalX * halfWidth, point[1] + .03, point[2] + normalZ * halfWidth,
      point[0] - normalX * halfWidth, point[1] + .03, point[2] - normalZ * halfWidth,
    );
  }
  for (let index = 0; index < end; index += 1) {
    const next = (index + 1) % usable.length;
    const left = index * 2;
    const right = left + 1;
    const nextLeft = next * 2;
    const nextRight = nextLeft + 1;
    indices.push(left, right, nextLeft, right, nextRight, nextLeft);
  }
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function TrackSurfaceMesh({ imageUrl, config, origin, surfaceY }: {
  imageUrl: string;
  config: NonNullable<TrackMap['map_config']>;
  origin: Vec3;
  surfaceY: number;
}) {
  const texture = useLoader(TextureLoader, imageUrl);
  texture.colorSpace = SRGBColorSpace;
  const transform = mapPlaneTransform(config, origin);
  return <mesh position={[transform.centerX, surfaceY, transform.centerZ]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
    <planeGeometry args={[transform.width, transform.height]}/>
    <meshBasicMaterial map={texture} transparent opacity={.2} depthWrite={false} side={DoubleSide}/>
  </mesh>;
}

function FocusedOrbitControls({ target }: { target: Vec3 }) {
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const { camera } = useThree();
  const initialized = useRef(false);
  const nextTarget = useRef(new Vector3());
  const desiredPosition = useRef(new Vector3());

  useFrame((_state, delta) => {
    const controls = controlsRef.current;
    if (!controls) return;
    if (!initialized.current) {
      camera.position.set(target[0] + 12, target[1] + 14, target[2] + 16);
      controls.target.set(...target);
      initialized.current = true;
      controls.update();
      return;
    }
    const followAmount = 1 - Math.exp(-delta * 12);
    nextTarget.current.set(...target);
    const cameraOffset = camera.position.clone().sub(controls.target);
    controls.target.lerp(nextTarget.current, followAmount);
    desiredPosition.current.copy(nextTarget.current).add(cameraOffset);
    camera.position.lerp(desiredPosition.current, followAmount);
    controls.update();
  });

  return <OrbitControls ref={controlsRef} makeDefault enableDamping dampingFactor={.09}
    maxPolarAngle={Math.PI / 2.05} minDistance={4} maxDistance={120}/>;
}

export function TrajectoryScene({ samples, selected, reference, trackMap, carName, carVisual, trackName }: {
  samples: TelemetrySample[];
  selected: TelemetrySample;
  reference: Vec3[];
  trackMap?: TrackMap | null;
  carName?: string;
  carVisual?: CarVisual | null;
  trackName?: string;
}) {
  const [proceduralFallback, setProceduralFallback] = useState(false);
  const handleModelFallback = useCallback((active: boolean) => setProceduralFallback(active), []);
// Subtracting the origin reduces WebGL precision errors with large map coordinates.
  const originRef = useRef<Vec3 | null>(null);
  if (originRef.current === null && samples.length) originRef.current = [...samples[0].position_world_m];
  const origin = originRef.current || samples[0].position_world_m;
  const points = useMemo(() => downsample(samples, 1600).map((s) => [
    s.position_world_m[0] - origin[0],
    s.position_world_m[1] - origin[1] + .07,
    s.position_world_m[2] - origin[2],
  ] as Vec3), [samples, origin]);
  const refPoints = useMemo(() => downsample(reference, 1200).map((p) => [
    p[0] - origin[0], p[1] - origin[1] + .11, p[2] - origin[2],
  ] as Vec3), [reference, origin]);
  const carX = selected.position_world_m[0] - origin[0];
  const carY = selected.position_world_m[1] - origin[1];
  const carZ = selected.position_world_m[2] - origin[2];
  const cameraTarget: Vec3 = [carX, carY + .45, carZ];
  return <div className="three-wrapper" role="img" aria-label="Cena 3D interativa do carro e sua trajetória">
    <Canvas shadows dpr={[1, 1.5]} gl={{ antialias: true, powerPreference: 'high-performance' }}>
      <color attach="background" args={['#0e1826']}/>
      <fog attach="fog" args={['#0e1826', 90, 320]}/>
      <ambientLight intensity={1.1}/>
      <directionalLight position={[12, 30, 9]} intensity={2.3} castShadow shadow-mapSize={[512,512]}/>
      <PerspectiveCamera makeDefault fov={48} near={.1} far={2000}/>
      <FocusedOrbitControls target={cameraTarget}/>
      <TrackSurface trackMap={trackMap} origin={origin}/>
      <Grid infiniteGrid cellSize={5} sectionSize={25} sectionColor="#36536a" cellColor="#23374c" fadeDistance={170} position={[0,-.25,0]}/>
      <axesHelper args={[6]}/>
      {points.length >= 2 && <Line points={points} color="#14cdb2" lineWidth={3}/>} 
      {refPoints.length >= 2 && <Line points={refPoints} color="#69a7fc" lineWidth={2.7} dashed dashSize={.8} gapSize={.6}/>} 
      <CarModel sample={selected} origin={origin} carName={carName} carVisual={carVisual} onModelFallback={handleModelFallback}/>
    </Canvas>
    <div className="scene-track-map">
      <TrackMiniMap samples={samples} selected={selected} reference={reference} trackMap={trackMap} trackName={trackName} compact/>
    </div>
    <div className="scene-car-label">
      {carVisual?.brand ? `${carVisual.brand} ` : ''}{carVisual?.display_name || carName || 'Carro detectado'} · {trackName || 'Pista atual'}
      {carVisual?.ui_metadata && <small> · conteúdo instalado{carVisual.model_format ? ` · modelo ${carVisual.model_format.toUpperCase()}` : ''}</small>}
      {carVisual?.skin_id && <small> · skin {carVisual.skin_id}</small>}
      {carVisual?.model_format === 'kn5' && <small> · fonte KN5 detectada; conversão automática quando compatível</small>}
      {proceduralFallback && <small> · fallback procedural ativo</small>}
    </div>
    <div className="scene-legend"><span><i style={{ background: '#14cdb2' }}/> Trajetória</span><span><i style={{ background: '#69a7fc' }}/> Referência</span></div>
    <div className="scene-hint">Arraste para girar a câmera · scroll para zoom</div>
  </div>;
}
