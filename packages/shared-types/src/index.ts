// ============================================
// NeuroTune AI - Types Partagés
// ============================================

// Types d'endianess
export enum Endianess {
  LITTLE = 'little',
  BIG = 'big'
}

// Formats de fichier ECU
export enum EcuFileFormat {
  BIN = 'BIN',
  HEX = 'HEX',
  SREC = 'SREC',
  A2L = 'A2L',
  DAMOS = 'DAMOS',
  KP = 'KP',
  OLS = 'OLS'
}

// Algorithmes de checksum
export enum ChecksumAlgorithm {
  CRC32 = 'CRC32',
  ADD16 = 'ADD16',
  XOR8 = 'XOR8',
  MD5 = 'MD5',
  SHA256 = 'SHA256'
}

// Types d'axes de maps
export enum MapAxisType {
  RPM = 'rpm',
  LOAD = 'load',
  TEMPERATURE = 'temperature',
  PRESSURE = 'pressure',
  FUEL_QUANTITY = 'fuel_quantity',
  IGNITION_ANGLE = 'ignition_angle',
  LAMBDA = 'lambda',
  BOOST = 'boost',
  TORQUE = 'torque',
  UNKNOWN = 'unknown'
}

// Structure ECU
export interface EcuStructure {
  mapsOffset: number;
  checksums: ChecksumRegion[];
  mapDescriptors: MapDescriptor[];
  metadata?: Record<string, any>;
}

export interface ChecksumRegion {
  algorithm: ChecksumAlgorithm;
  start: number;
  end: number;
  location: number;
  size: number;
}

export interface MapDescriptor {
  axisType: MapAxisType;
  valueType: MapAxisType;
  defaultAxisSize: number;
}

// Identification ECU
export interface EcuIdentification {
  manufacturer: string;
  ecuType: string;
  softwareVersion: string;
  hardwareNumber: string;
  vin?: string;
  calibrationId?: string;
}

// Map parsée
export interface ParsedMap {
  offset: number;
  axis: number[];
  values: number[];
  type: '1D' | '2D' | '3D';
  axisSize: number;
  valueSize: number;
  format: string;
  metadata?: Record<string, any>;
}

// Map canonique (DTO interne)
export interface CanonicalMapDTO {
  id: string;
  name: string;
  type: string;
  address: number;
  axes: MapAxis[];
  values: number[];
  metadata: MapMetadata;
}

export interface MapAxis {
  name: string;
  unit: string;
  values: number[];
}

export interface MapMetadata {
  source: string;
  conversionDate: string;
  originalFormat: string;
  ecuType?: string;
  softwareVersion?: string;
  axisNames?: string[];
  axisUnits?: string[];
}

// Projet WinOLS
export interface WinOLSProject {
  version: string;
  metadata: MapConversionMetadata;
  maps: KPMap[];
  checksums: any[];
}

export interface MapConversionMetadata {
  ecuType?: string;
  softwareVersion?: string;
  axisNames?: string[];
  axisUnits?: string[];
}

export interface KPMap {
  name: string;
  address: number;
  axisCount: number;
  axisSize: number;
  axes: number[][];
  values: number[];
  size: number;
}

export interface OLSMap {
  name: string;
  address: number;
  type: number;
  data: Buffer;
}

// Types de projet
export enum ProjectStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  LOCKED = 'locked'
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  TUNER = 'tuner',
  VIEWER = 'viewer'
}

// Types pour l'API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  pageSize: number;
}

// Types pour la sécurité
export interface JwtPayload {
  userId: string;
  tenantId: string;
  role: UserRole;
  permissions: string[];
}

// Types pour les simulations
export interface SimulationParameters {
  rpm: number;
  load: number;
  lambda: number;
  ignitionAngle: number;
  boostPressure: number;
  intakeTemp: number;
  coolantTemp: number;
  exhaustBackpressure: number;
  duration: number;
}

export interface SimulationResult {
  torque: number[];
  power: number[];
  egt: number[];
  lambda: number[];
  boost: number[];
  timeStamps: number[];
}

// Types pour l'IA
export interface AIAnalysisResult {
  mapDetections: any[];
  afrPredictions: any[];
  egtEstimations: any[];
  recommendations: string[];
  safetyScore: number;
  confidence: number;
}

// Types CAN Bus
export interface CANMessage {
  id: number;
  timestamp: number;
  data: Buffer;
  dlc: number;
  interface?: string;
}

// Types de base de données (pour Prisma)
export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl?: boolean;
}