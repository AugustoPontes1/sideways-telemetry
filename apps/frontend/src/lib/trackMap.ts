import type { TrackMap, Vec3 } from './types';

export interface MapPoint {
  x: number;
  y: number;
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function mapScale(config: NonNullable<TrackMap['map_config']>): number {
  return config.scale_factor > 0 ? config.scale_factor : 1;
}

export function acHeadingToSceneYaw(heading: number): number {
  return -heading - Math.PI;
}

export function acHeadingToMapDegrees(heading: number): number {
  return (heading + Math.PI) * 180 / Math.PI;
}

export function projectWorldToMap(
  point: Vec3 | [number, number],
  config: NonNullable<TrackMap['map_config']>,
): MapPoint {
  const scale = mapScale(config);
  const worldX = point[0] * scale + config.offset_x;
  const worldZ = point.length === 3 ? point[2] * scale + config.offset_z : point[1] * scale + config.offset_z;
  return {
    x: clamp((worldX / config.width) * 100),
    y: clamp((worldZ / config.height) * 100),
  };
}

export function mapPlaneTransform(
  config: NonNullable<TrackMap['map_config']>,
  origin: Vec3,
): { width: number; height: number; centerX: number; centerZ: number } {
  const scale = mapScale(config);
  return {
    width: config.width / scale,
    height: config.height / scale,
    centerX: (config.width / 2 - config.offset_x) / scale - origin[0],
    centerZ: (config.height / 2 - config.offset_z) / scale - origin[2],
  };
}
