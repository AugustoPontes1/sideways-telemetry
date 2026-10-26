import { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { Grid, Line, OrbitControls, PerspectiveCamera } from '@react-three/drei';
import type { TelemetrySample, Vec3 } from '../../lib/types';
import { downsample } from '../../lib/telemetry';
import { CarModel } from './CarModel';

export function TrajectoryScene({ samples, selected, reference }: {
  samples: TelemetrySample[];
  selected: TelemetrySample;
  reference: Vec3[];
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
    <Canvas shadows dpr={[1, 1.8]} gl={{ antialias: true }}>
      <color attach="background" args={['#0e1826']}/>
      <fog attach="fog" args={['#0e1826', 90, 320]}/>
      <ambientLight intensity={1.1}/>
      <directionalLight position={[12, 30, 9]} intensity={2.3} castShadow shadow-mapSize={[1024,1024]}/>
      <PerspectiveCamera makeDefault position={[carX + 24, 26, carZ + 28]} fov={48} near={.1} far={2000}/>
      <OrbitControls makeDefault target={[carX, 0, carZ]} enableDamping dampingFactor={.09} maxPolarAngle={Math.PI / 2.05} minDistance={8} maxDistance={220}/>
      <Grid infiniteGrid cellSize={5} sectionSize={25} sectionColor="#36536a" cellColor="#23374c" fadeDistance={170} position={[0,-.25,0]}/>
      <axesHelper args={[6]}/>
      {points.length >= 2 && <Line points={points} color="#14cdb2" lineWidth={3}/>} 
      {refPoints.length >= 2 && <Line points={refPoints} color="#69a7fc" lineWidth={2.7} dashed dashSize={.8} gapSize={.6}/>} 
      <CarModel sample={selected} origin={origin}/>
    </Canvas>
    <div className="scene-legend"><span><i style={{ background: '#14cdb2' }}/> Trajetória</span><span><i style={{ background: '#69a7fc' }}/> Referência</span></div>
    <div className="scene-hint">Arraste para girar a câmera · scroll para zoom</div>
  </div>;
}
