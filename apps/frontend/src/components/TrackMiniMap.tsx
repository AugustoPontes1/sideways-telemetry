import { useMemo } from 'react';
import { downsample } from '../lib/telemetry';
import type { TelemetrySample, TrackMap, Vec3 } from '../lib/types';

interface TrackMiniMapProps {
  samples: TelemetrySample[];
  selected?: TelemetrySample | null;
  reference?: Vec3[];
  trackMap?: TrackMap | null;
  trackName?: string;
  compact?: boolean;
}

interface MapPoint {
  x: number;
  y: number;
}

interface Bounds {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
  centerX: number;
  centerZ: number;
  span: number;
}

function boundsFor(points: Array<[number, number]>): Bounds | null {
  if (!points.length) return null;
  const minX = Math.min(...points.map(([x]) => x));
  const maxX = Math.max(...points.map(([x]) => x));
  const minZ = Math.min(...points.map(([, z]) => z));
  const maxZ = Math.max(...points.map(([, z]) => z));
  const centerX = (minX + maxX) / 2;
  const centerZ = (minZ + maxZ) / 2;
  const span = Math.max(maxX - minX, maxZ - minZ, 1);
  return { minX, maxX, minZ, maxZ, centerX, centerZ, span };
}

function projectPoint([x, z]: [number, number], bounds: Bounds): MapPoint {
  return {
    x: 50 + ((x - bounds.centerX) / bounds.span) * 78,
    y: 50 - ((z - bounds.centerZ) / bounds.span) * 78,
  };
}

function project(points: Array<[number, number]>, bounds: Bounds | null): MapPoint[] {
  if (!bounds) return [];
  return points.map(([x, z]) => ({
    x: 50 + ((x - bounds.centerX) / bounds.span) * 78,
    y: 50 - ((z - bounds.centerZ) / bounds.span) * 78,
  }));
}

function projectMapPoint([x, z]: [number, number], config: NonNullable<TrackMap['map_config']>): MapPoint {
  return {
    x: Math.max(0, Math.min(100, ((x + config.offset_x) / config.width) * 100)),
    y: Math.max(0, Math.min(100, ((z + config.offset_z) / config.height) * 100)),
  };
}

function pointString(points: MapPoint[]): string {
  return points.map(({ x, y }) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
}

export function TrackMiniMap({ samples, selected, reference = [], trackMap, trackName, compact = false }: TrackMiniMapProps) {
  const map = useMemo(() => {
    const capturedRoute = downsample(samples, 900).map((sample) => [sample.position_world_m[0], sample.position_world_m[2]] as [number, number]);
    const fullTrack = trackMap && Array.isArray(trackMap.points) && trackMap.points.length >= 2
      ? downsample(trackMap.points, 1200).map((point) => [point[0], point[2]] as [number, number])
      : [];
    const hasFullMap = Boolean(fullTrack.length >= 2 || trackMap?.image_url);
    const route = fullTrack.length >= 2
      ? fullTrack
      : capturedRoute;
    const referenceRoute = hasFullMap ? [] : downsample(reference, 900).map((point) => [point[0], point[2]] as [number, number]);
    const all = [...route, ...referenceRoute];
    const selectedRoutePoint = selected ? [selected.position_world_m[0], selected.position_world_m[2]] as [number, number] : null;
    const bounds = boundsFor(all);
    const projected = project(all, bounds);
    const routeEnd = route.length;
    const selectedPoint = selectedRoutePoint && bounds ? projectPoint(selectedRoutePoint, bounds) : null;
    const mapConfig = trackMap?.map_config;
    const mapSelectedPoint = selectedRoutePoint && trackMap?.image_url && mapConfig
      ? projectMapPoint(selectedRoutePoint, mapConfig)
      : selectedPoint;
    return {
      route: projected.slice(0, routeEnd),
      reference: projected.slice(routeEnd, routeEnd + referenceRoute.length),
      selected: mapSelectedPoint,
      full: hasFullMap,
      source: trackMap?.source || '',
      imageUrl: trackMap?.image_url || '',
    };
  }, [reference, samples, selected, trackMap]);

  if (map.route.length < 2 && !map.imageUrl) {
    return <div className={`track-minimap ${compact ? 'compact' : ''}`}>
      <div className="track-minimap-empty">Aguardando pontos suficientes para desenhar o traçado.</div>
    </div>;
  }

  return <div className={`track-minimap ${compact ? 'compact' : ''}`}>
    {!compact && <div className="track-minimap-heading"><span>{map.full ? 'MAPA COMPLETO DA PISTA' : 'MAPA DO TRAÇADO CAPTURADO'}</span><strong>{trackName || 'Pista atual'}{map.full && map.source ? ` · ${map.source}` : ''}</strong></div>}
    <div className="track-map-canvas">
      {map.imageUrl && <img className="track-map-image" src={map.imageUrl} alt={`Mapa completo da pista ${trackName || ''}`} />}
      <svg viewBox="0 0 100 100" role="img" aria-label={`${map.full ? 'Mapa completo' : 'Traçado capturado'} da pista ${trackName || ''}`}>
        <polyline className="track-map-reference" points={pointString(map.reference)} fill="none"/>
        <polyline className="track-map-shadow" points={pointString(map.route)} fill="none"/>
        <polyline className="track-map-route" points={pointString(map.route)} fill="none"/>
        {map.route[0] && <circle className="track-map-start" cx={map.route[0].x} cy={map.route[0].y} r="2.1"/>}
        {map.selected && <g className="track-map-car" aria-label="Posição atual do carro">
          <title>Posição atual do carro</title>
          <circle className="track-map-current-pulse" cx={map.selected.x} cy={map.selected.y} r="5.5"/>
          <circle className="track-map-current" cx={map.selected.x} cy={map.selected.y} r="3.2"/>
        </g>}
      </svg>
    </div>
    {!compact && <div className="track-minimap-legend"><span><i className="route"/> {map.full ? 'Pista completa' : 'Capturado'}</span>{!map.full && <span><i className="reference"/> Referência</span>}</div>}
  </div>;
}
