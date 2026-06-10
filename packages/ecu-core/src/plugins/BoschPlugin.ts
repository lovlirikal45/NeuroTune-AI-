import { Buffer } from 'buffer';
import { BaseEcuPlugin } from './BasePlugin';
import { 
  EcuStructure, 
  ChecksumAlgorithm, 
  MapAxisType,
  ParsedMap 
} from '@neurotune/shared-types';

export class BoschPlugin extends BaseEcuPlugin {
  manufacturer = 'Bosch';
  supportedEcus = [
    'ME7.x',
    'MED9.x',
    'MED17.x',
    'EDC16',
    'EDC17',
    'MEVD17.x'
  ];

  protected identificationPatterns = [
    /1037(?:3[0-9]|4[0-5])(?<type>[A-Z0-9]{4})(?<version>[A-Z0-9]{4})/,
    /0261(?:2[0-9]|3[0-9])(?<hardware>[A-Z0-9]{10})/
  ];

  protected ecuStructures = new Map<string, EcuStructure>([
    ['ME7.5', {
      mapsOffset: 0x10000,
      checksums: [
        {
          algorithm: ChecksumAlgorithm.CRC32,
          start: 0x8000,
          end: 0xFFFF,
          location: 0x8000,
          size: 4
        }
      ],
      mapDescriptors: [
        {
          axisType: MapAxisType.RPM,
          valueType: MapAxisType.FUEL_QUANTITY,
          defaultAxisSize: 16
        },
        {
          axisType: MapAxisType.LOAD,
          valueType: MapAxisType.IGNITION_ANGLE,
          defaultAxisSize: 16
        }
      ]
    }]
  ]);

  async parseStructure(buffer: Buffer): Promise<EcuStructure> {
    const ecuType = this.detectEcuType(buffer);
    const structure = this.ecuStructures.get(ecuType);
    
    if (!structure) {
      throw new Error(`Unknown ECU type: ${ecuType}`);
    }

    return structure;
  }

  async extractMaps(buffer: Buffer, structure: EcuStructure): Promise<ParsedMap[]> {
    const maps: ParsedMap[] = [];
    
    for (let offset = structure.mapsOffset; offset < buffer.length - 256; offset += 2) {
      const potentialMap = this.analyzeMapCandidate(buffer, offset);
      if (potentialMap) {
        maps.push(potentialMap);
      }
    }

    return maps;
  }

  private detectEcuType(buffer: Buffer): string {
    const header = buffer.toString('ascii', 0, 100);
    
    if (header.includes('ME7.')) return 'ME7.5';
    if (header.includes('MED9')) return 'MED9.1';
    if (header.includes('MED17')) return 'MED17.5';
    if (header.includes('EDC16')) return 'EDC16';
    
    return 'ME7.5';
  }

  private analyzeMapCandidate(buffer: Buffer, offset: number): ParsedMap | null {
    const axisSize = buffer.readUInt8(offset);
    
    if (axisSize < 4 || axisSize > 32) return null;
    
    const axisValues: number[] = [];
    for (let i = 0; i < axisSize; i++) {
      const value = buffer.readUInt16LE(offset + 1 + i * 2);
      if (i > 0 && value <= axisValues[i - 1]) return null;
      axisValues.push(value);
    }

    return {
      offset,
      axis: axisValues,
      values: new Array(axisSize).fill(0),
      type: '2D',
      axisSize,
      valueSize: 2,
      format: 'BOSCH_ME7'
    };
  }

  async validateChecksums(buffer: Buffer): Promise<boolean> {
    const structure = await this.parseStructure(buffer);
    
    for (const checksum of structure.checksums) {
      const calculated = this.calculateBoschChecksum(buffer, checksum.start, checksum.end);
      const stored = buffer.readUInt32LE(checksum.location);
      
      if (calculated !== stored) return false;
    }

    return true;
  }

  async correctChecksums(buffer: Buffer): Promise<Buffer> {
    const corrected = Buffer.from(buffer);
    const structure = await this.parseStructure(buffer);
    
    for (const checksum of structure.checksums) {
      const calculated = this.calculateBoschChecksum(corrected, checksum.start, checksum.end);
      corrected.writeUInt32LE(calculated, checksum.location);
    }

    return corrected;
  }

  private calculateBoschChecksum(buffer: Buffer, start: number, end: number): number {
    let sum = 0;
    for (let i = start; i < end; i += 4) {
      sum += buffer.readUInt32LE(i);
    }
    return sum >>> 0;
  }
}