import { useMemo } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { Grid, Line, OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { DoubleSide, SRGBColorSpace, TextureLoader } from 'three';
import type { CarVisual, TelemetrySample, TrackMap, Vec3 } from '../../lib/types';
import { downsample } from '../../lib/telemetry';
import { TrackMiniMap } from '../../components/TrackMiniMap';
import { CarModel } from './CarModel';

function TrackSurface({ trackMap, origin }: { trackMap?: TrackMap | null; origin: Vec3 }) {
  const imageUrl = trackMap?.image_url;
  const config = trackMap?.map_config;
  const trackPoints = useMemo(() => downsample(trackMap?.points || [], 1600).map((point) => [
    point[0] - origin[0],
    point[1] - origin[1] - .16,
    point[2] - origin[2],
  ] as Vec3), [origin, trackMap]);
  return <>
    {imageUrl && config && <TrackSurfaceMesh imageUrl={imageUrl} config={config} origin={origin}/>}
    {trackPoints.length >= 2 && <Line points={trackPoints} color="#547087" lineWidth={1.5} transparent opacity={.65}/>}
  </>;
}

function TrackSurfaceMesh({ imageUrl, config, origin }: {
  imageUrl: string;
  config: NonNullable<TrackMap['map_config']>;
  origin: Vec3;
}) {
  const texture = useLoader(TextureLoader, imageUrl);
  texture.colorSpace = SRGBColorSpace;
  const centerX = config.width / 2 - config.offset_x - origin[0];
  const centerZ = config.height / 2 - config.offset_z - origin[2];
  return <mesh position={[centerX, -0.32, centerZ]} rotation={[Math.PI / 2, 0, 0]} receiveShadow>
    <planeGeometry args={[config.width, config.height]}/>
    <meshBasicMaterial map={texture} transparent opacity={.72} depthWrite={false} side={DoubleSide}/>
  </mesh>;
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
// Subtracting the origin reduces WebGL precision errors with large map coordinates.
  const origin = useMemo<[number, number, number]>(() => [...samples[0].position_world_m], [samples]);
  const points = useMemo(() => downsample(samples, 1600).map((s) => [
    s.position_world_m[0] - origin[0],
    s.position_world_m[1] - origin[1] + .07,
    s.position_world_m[2] - origin[2],
  ] as Vec3), [samples, origin]);
  const refPoints = useMemo(() => downsample(reference, 1200).map((p) => [
    p[0] - origin[0], p[1] - origin[1] + .11, p[2] - origin[2],
  ] as Vec3), [reference, origin]);
  const carX = selected.position_world_m[0] - origin[0];
  const carZ = selected.position_world_m[2] - origin[2];
  return <div className="three-wrapper" role="img" aria-label="Cena 3D interativa do carro e sua trajetória">
    <Canvas shadows dpr={[1, 1.5]} gl={{ antialias: true, powerPreference: 'high-performance' }}>
      <color attach="background" args={['#0e1826']}/>
      <fog attach="fog" args={['#0e1826', 90, 320]}/>
      <ambientLight intensity={1.1}/>
      <directionalLight position={[12, 30, 9]} intensity={2.3} castShadow shadow-mapSize={[512,512]}/>
      <PerspectiveCamera makeDefault position={[carX + 24, 26, carZ + 28]} fov={48} near={.1} far={2000}/>
      <OrbitControls makeDefault target={[carX, 0, carZ]} enableDamping dampingFactor={.09} maxPolarAngle={Math.PI / 2.05} minDistance={8} maxDistance={220}/>
      <TrackSurface trackMap={trackMap} origin={origin}/>
      <Grid infiniteGrid cellSize={5} sectionSize={25} sectionColor="#36536a" cellColor="#23374c" fadeDistance={170} position={[0,-.25,0]}/>
      <axesHelper args={[6]}/>
      {points.length >= 2 && <Line points={points} color="#14cdb2" lineWidth={3}/>} 
      {refPoints.length >= 2 && <Line points={refPoints} color="#69a7fc" lineWidth={2.7} dashed dashSize={.8} gapSize={.6}/>} 
      <CarModel sample={selected} origin={origin} carName={carName} carVisual={carVisual}/>
    </Canvas>
    <div className="scene-track-map">
      <TrackMiniMap samples={samples} selected={selected} reference={reference} trackMap={trackMap} trackName={trackName} compact/>
    </div>
    <div className="scene-car-label">
      {carVisual?.brand ? `${carVisual.brand} ` : ''}{carVisual?.display_name || carName || 'Carro detectado'} · {trackName || 'Pista atual'}
      {carVisual?.ui_metadata && <small> · conteúdo instalado{carVisual.model_format ? ` · modelo ${carVisual.model_format.toUpperCase()}` : ''}</small>}
      {carVisual?.skin_id && <small> · skin {carVisual.skin_id}</small>}
      {carVisual?.model_format === 'kn5' && <small> · fonte KN5 detectada; conversão automática quando compatível</small>}
    </div>
    <div className="scene-legend"><span><i style={{ background: '#14cdb2' }}/> Trajetória</span><span><i style={{ background: '#69a7fc' }}/> Referência</span></div>
    <div className="scene-hint">Arraste para girar a câmera · scroll para zoom</div>
  </div>;
}
