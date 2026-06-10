import { Buffer } from 'buffer';
import { 
  Endianess, 
  ParsedMap, 
  ChecksumAlgorithm,
  EcuStructure 
} from '@neurotune/shared-types';

export interface ParserOptions {
  endianess?: Endianess;
  detectEndianess?: boolean;
  validateChecksums?: boolean;
  maxFileSize?: number;
}

export class BinaryParser {
  private buffer: Buffer;
  private endianess: Endianess;
  private structure: EcuStructure | null = null;

  constructor(data: Buffer, options: ParserOptions = {}) {
    if (options.maxFileSize && data.length > options.maxFileSize) {
      throw new Error(`File size exceeds maximum: ${data.length} bytes`);
    }

    this.buffer = data;
    this.endianess = options.endianess || Endianess.LITTLE;
    
    if (options.detectEndianess) {
      this.endianess = this.detectEndianess();
    }
  }

  /**
   * Détecte l'endianess du fichier binaire
   */
  private detectEndianess(): Endianess {
    // Patterns communs pour la détection
    const signatures = {
      littleEndian: [0x00, 0x00, 0x00, 0x10],
      bigEndian: [0x10, 0x00, 0x00, 0x00]
    };

    for (let i = 0; i < Math.min(this.buffer.length - 4, 1024); i++) {
      const slice = Array.from(this.buffer.slice(i, i + 4));
      
      if (this.compareSignature(slice, signatures.littleEndian)) {
        return Endianess.LITTLE;
      }
      if (this.compareSignature(slice, signatures.bigEndian)) {
        return Endianess.BIG;
      }
    }

    return Endianess.LITTLE; // Défaut
  }

  private compareSignature(buffer: number[], signature: number[]): boolean {
    return signature.every((byte, index) => buffer[index] === byte);
  }

  /**
   * Lit une valeur avec gestion de l'endianess
   */
  readValue(offset: number, size: number, signed: boolean = false): number {
    if (offset + size > this.buffer.length) {
      throw new Error(`Read exceeds buffer bounds: offset=${offset}, size=${size}`);
    }

    const slice = this.buffer.slice(offset, offset + size);
    let value = 0;

    for (let i = 0; i < size; i++) {
      const byte = slice[i];
      const shift = this.endianess === Endianess.LITTLE ? i * 8 : (size - 1 - i) * 8;
      value |= byte << shift;
    }

    if (signed && (value & (1 << (size * 8 - 1)))) {
      value -= 1 << (size * 8);
    }

    return value;
  }

  /**
   * Calcule un checksum
   */
  calculateChecksum(start: number, end: number, algorithm: ChecksumAlgorithm): number {
    const region = this.buffer.slice(start, end);
    
    switch (algorithm) {
      case ChecksumAlgorithm.CRC32:
        return this.crc32(region);
      case ChecksumAlgorithm.ADD16:
        return this.additive16(region);
      case ChecksumAlgorithm.XOR8:
        return this.xor8(region);
      default:
        throw new Error(`Unsupported checksum algorithm: ${algorithm}`);
    }
  }

  private crc32(data: Buffer): number {
    let crc = 0xFFFFFFFF;
    for (const byte of data) {
      crc ^= byte;
      for (let i = 0; i < 8; i++) {
        crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
      }
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  private additive16(data: Buffer): number {
    let sum = 0;
    for (let i = 0; i < data.length - 1; i += 2) {
      sum += data.readUInt16LE(i);
    }
    return sum & 0xFFFF;
  }

  private xor8(data: Buffer): number {
    return data.reduce((acc, byte) => acc ^ byte, 0);
  }

  /**
   * Recherche des maps 2D dans le binaire
   */
  find2DMaps(axisSize: number, valueSize: number): ParsedMap[] {
    const maps: ParsedMap[] = [];
    const stride = axisSize * 2 + (axisSize * valueSize);
    
    for (let offset = 0; offset < this.buffer.length - stride; offset += 2) {
      if (this.isValidMapPattern(offset, axisSize, valueSize)) {
        maps.push(this.extractMap(offset, axisSize, valueSize));
      }
    }

    return maps;
  }

  private isValidMapPattern(offset: number, axisSize: number, valueSize: number): boolean {
    const axisValues: number[] = [];
    for (let i = 0; i < axisSize; i++) {
      axisValues.push(this.readValue(offset + i * 2, 2));
    }

    // Vérifier la monotonie
    for (let i = 1; i < axisValues.length; i++) {
      if (axisValues[i] <= axisValues[i - 1]) return false;
    }

    // Vérifier les valeurs dans une plage raisonnable
    const mapStart = offset + axisSize * 2;
    for (let i = 0; i < axisSize; i++) {
      const value = this.readValue(mapStart + i * valueSize, valueSize);
      if (value < -10000 || value > 100000) return false;
    }

    return true;
  }

  private extractMap(offset: number, axisSize: number, valueSize: number): ParsedMap {
    const axis: number[] = [];
    const values: number[] = [];

    for (let i = 0; i < axisSize; i++) {
      axis.push(this.readValue(offset + i * 2, 2));
    }

    const mapStart = offset + axisSize * 2;
    for (let i = 0; i < axisSize; i++) {
      values.push(this.readValue(mapStart + i * valueSize, valueSize));
    }

    return {
      offset,
      axis,
      values,
      type: '2D',
      axisSize,
      valueSize,
      format: 'RAW'
    };
  }

  /**
   * Valide la structure complète du fichier ECU
   */
  validateStructure(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (this.buffer.length < 1024) {
      errors.push('File too small to be a valid ECU binary');
    }

    const magicBytes = this.buffer.slice(0, 4).toString('hex');
    if (!['00000010', '10000000'].includes(magicBytes)) {
      errors.push(`Unknown magic bytes: ${magicBytes}`);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  getBuffer(): Buffer {
    return this.buffer;
  }

  getEndianess(): Endianess {
    return this.endianess;
  }
}