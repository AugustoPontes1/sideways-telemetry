export type Vec3 = [number, number, number];
export type DamageZones = [number, number, number, number, number];

export interface TrackMap {
  source: string;
  points: Vec3[];
  image_url?: string;
  map_config?: {
    width: number;
    height: number;
    offset_x: number;
    offset_z: number;
    scale_factor: number;
  };
}

export interface CarVisual {
  id: string;
  display_name: string;
  brand: string;
  asset_key: string;
  source: string;
  ui_metadata: boolean;
  model_format: string;
  skin_id?: string;
  color_hex?: string;
}

export interface DrivingSession {
  stream_id: string;
  agent_id: string;
  car: string;
  track: string;
  car_visual?: CarVisual | null;
  session_type: number;
  sample_count: number;
  max_sequence: number;
  first_sample_at: string;
  last_sample_at: string;
  created_at: string;
  updated_at: string;
}

/** Unified DTO: REST provides sampled_at; WS publishes timestamp_unix_ns. */
export interface TelemetrySample {
  sequence: number;
  sampled_at: string;
  received_at?: string;
  speed_kmh: number;
  speed_mps: number;
  rpm: number;
  gear: number;
  throttle: number;
  brake: number;
  clutch: number;
  steer_angle_rad: number;
  heading_rad: number;
  pitch_rad?: number;
  roll_rad?: number;
  position_world_m: Vec3;
  velocity_world_mps: Vec3;
  car_damage: DamageZones;
  completed_laps?: number;
}

export interface SamplesPage {
  stream_id: string;
  samples: TelemetrySample[];
  has_more: boolean;
  next_after: number | null;
}

export interface LiveMessage {
  type: 'telemetry.samples';
  stream_id: string;
  samples: Array<Partial<TelemetrySample> & {
    sequence: number;
    timestamp_unix_ns: number;
  }>;
}

export type LiveStatus = 'demo' | 'connecting' | 'connected' | 'reconnecting' | 'offline';

export interface AnalysisStats {
  count: number;
  speed_min_kmh: number | null;
  speed_max_kmh: number | null;
  speed_avg_kmh: number | null;
  rpm_min: number | null;
  rpm_max: number | null;
  throttle_avg: number | null;
}
export interface DriverEvent {
  kind: string;
  sequence: number;
  rate: number;
  unit: string;
  label: string;
}
export interface SessionAnalysis {
  stream_id: string;
  car: string;
  track: string;
  stats: AnalysisStats;
  events: DriverEvent[];
  event_window_samples: number;
  interpretation: string;
}
export interface TrajectoryComparison {
  evaluated_points: number;
  mean_distance_m: number;
  max_distance_m: number;
  per_point_distance_m: number[];
  actual_path_xz_m: [number, number][];
  reference_path_xz_m: [number, number][];
  method: string;
  limitations: string;
  current_stream_id: string;
  reference_stream_id: string;
}
export interface LearningTopic {
  id: string;
  title: string;
  lessons: number[];
}
export type ExerciseValue = null | string | number | boolean | ExerciseValue[] | { [key: string]: ExerciseValue };
export interface ExerciseCalculation {
  direction_vector: number[];
  unit: string;
  norm: number;
  angle_deg_from_x: number | null;
  parametric_form: string;
  multiples: Array<{ t: number; vector: number[] }>;
  basis: number[][];
}
export interface BasisDimensionCalculation {
  sample_sequences: number[];
  sample_speed_mps: number[];
  v1: number[];
  v2: number[];
  matrix: number[][];
  determinant: number;
  basis: number[][];
  dimension: number;
  numeric_tolerance: number;
}
export interface BasisDimension3DCalculation {
  sample_sequences: number[];
  sample_speed_mps: number[];
  vectors: number[][];
  matrix: number[][];
  determinant: number;
  basis: number[][];
  dimension: number;
  numeric_tolerance: number;
}
export interface Exercise {
  topic: string;
  title: string;
  lessons: number[];
  source_sequences: number[];
  question: string;
  inputs: Record<string, ExerciseValue>;
  expected_result: ExerciseValue;
  calculation?: ExerciseCalculation | BasisDimensionCalculation | BasisDimension3DCalculation;
  note: string;
  solution?: string[];
}
export interface AnswerCheck {
  correct: boolean;
  expected_result: ExerciseValue;
  solution_revealed: boolean;
}
