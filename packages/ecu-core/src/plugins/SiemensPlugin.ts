import { Buffer } from 'buffer';
import { BaseEcuPlugin } from './BasePlugin';
import { EcuStructure, ChecksumAlgorithm, MapAxisType, ParsedMap } from '@neurotune/shared-types';

export class SiemensPlugin extends BaseEcuPlugin {
  manufacturer = 'Siemens';
  supportedEcus = ['MS4x', 'MSS5x', 'MSD8x'];

  protected identificationPatterns = [
    /SIEMENS(?<type>[A-Z0-9]{4})(?<version>[0-9]{2})/,
    /5WK9[0-9]{3}(?<hardware>[A-Z0-9]{6})/
  ];

  protected ecuStructures = new Map<string, EcuStructure>([
    ['MS42', {
      mapsOffset: 0x8000,
      checksums: [
        {
          algorithm: ChecksumAlgorithm.ADD16,
          start: 0x6000,
          end: 0xFFFF,
          location: 0x7FFE,
          size: 2
        }
      ],
      mapDescriptors: [
        {
          axisType: MapAxisType.RPM,
          valueType: MapAxisType.FUEL_QUANTITY,
          defaultAxisSize: 16
        }
      ]
    }]
  ]);

  async parseStructure(buffer: Buffer): Promise<EcuStructure> {
    const ecuType = this.detectEcuType(buffer);
    const structure = this.ecuStructures.get(ecuType);
    
    if (!structure) {
      throw new Error(`Unknown Siemens ECU type: ${ecuType}`);
    }

    return structure;
  }

  async extractMaps(buffer: Buffer, structure: EcuStructure): Promise<ParsedMap[]> {
    const maps: ParsedMap[] = [];
    // Logique spécifique Siemens
    for (let offset = structure.mapsOffset; offset < buffer.length - 512; offset += 16) {
      const candidate = this.analyzeSiemensMap(buffer, offset);
      if (candidate) maps.push(candidate);
    }
    return maps;
  }

  private detectEcuType(buffer: Buffer): string {
    const header = buffer.toString('ascii', 0, 50);
    if (header.includes('MS42')) return 'MS42';
    if (header.includes('MS43')) return 'MS43';
    return 'MS42';
  }

  private analyzeSiemensMap(buffer: Buffer, offset: number): ParsedMap | null {
    // Logique spécifique Siemens pour la détection de maps
    const identifier = buffer.readUInt16BE(offset);
    if (identifier !== 0x5A5A) return null; // Magic number Siemens
    
    const axisSize = buffer.readUInt8(offset + 2);
    if (axisSize < 4 || axisSize > 24) return null;
    
    return {
      offset,
      axis: [],
      values: [],
      type: '2D',
      axisSize,
      valueSize: 2,
      format: 'SIEMENS_MS4x'
    };
  }

  async validateChecksums(buffer: Buffer): Promise<boolean> {
    const structure = await this.parseStructure(buffer);
    
    for (const checksum of structure.checksums) {
      const calculated = this.calculateSiemensChecksum(buffer, checksum.start, checksum.end);
      const stored = buffer.readUInt16LE(checksum.location);
      
      if (calculated !== stored) return false;
    }

    return true;
  }

  async correctChecksums(buffer: Buffer): Promise<Buffer> {
    const corrected = Buffer.from(buffer);
    const structure = await this.parseStructure(buffer);
    
    for (const checksum of structure.checksums) {
      const calculated = this.calculateSiemensChecksum(corrected, checksum.start, checksum.end);
      corrected.writeUInt16LE(calculated, checksum.location);
    }

    return corrected;
  }

  private calculateSiemensChecksum(buffer: Buffer, start: number, end: number): number {
    let sum = 0;
    for (let i = start; i < end; i += 2) {
      sum = (sum + buffer.readUInt16LE(i)) & 0xFFFF;
    }
    return (0x10000 - sum) & 0xFFFF;
  }
}