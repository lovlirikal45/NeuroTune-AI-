import { Buffer } from 'buffer';
import { BaseEcuPlugin } from './BasePlugin';
import { EcuStructure, ChecksumAlgorithm, MapAxisType, ParsedMap } from '@neurotune/shared-types';

export class DelphiPlugin extends BaseEcuPlugin {
  manufacturer = 'Delphi';
  supportedEcus = ['MT05', 'MT35', 'DCM3.x'];

  protected identificationPatterns = [
    /DELPHI(?<type>[A-Z0-9]{4})(?<version>[0-9]{3})/,
    /MT[0-9]{2}(?<hardware>[A-Z0-9]{8})/
  ];

  protected ecuStructures = new Map<string, EcuStructure>([
    ['MT05', {
      mapsOffset: 0x10000,
      checksums: [
        {
          algorithm: ChecksumAlgorithm.CRC32,
          start: 0x8000,
          end: 0x1FFFF,
          location: 0x7FFC,
          size: 4
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
      throw new Error(`Unknown Delphi ECU type: ${ecuType}`);
    }

    return structure;
  }

  async extractMaps(buffer: Buffer, structure: EcuStructure): Promise<ParsedMap[]> {
    const maps: ParsedMap[] = [];
    
    for (let offset = structure.mapsOffset; offset < buffer.length - 512; offset += 32) {
      const candidate = this.analyzeDelphiMap(buffer, offset);
      if (candidate) maps.push(candidate);
    }
    
    return maps;
  }

  private detectEcuType(buffer: Buffer): string {
    const header = buffer.toString('ascii', 0, 50);
    if (header.includes('MT05')) return 'MT05';
    if (header.includes('MT35')) return 'MT35';
    return 'MT05';
  }

  private analyzeDelphiMap(buffer: Buffer, offset: number): ParsedMap | null {
    const magic = buffer.readUInt32LE(offset);
    if (magic !== 0x44454C50) return null; // "DELP" en ASCII
    
    return {
      offset,
      axis: [],
      values: [],
      type: '2D',
      axisSize: 16,
      valueSize: 2,
      format: 'DELPHI_MT'
    };
  }

  async validateChecksums(buffer: Buffer): Promise<boolean> {
    const structure = await this.parseStructure(buffer);
    
    for (const checksum of structure.checksums) {
      const calculated = this.calculateDelphiChecksum(buffer, checksum.start, checksum.end);
      const stored = buffer.readUInt32LE(checksum.location);
      
      if (calculated !== stored) return false;
    }

    return true;
  }

  async correctChecksums(buffer: Buffer): Promise<Buffer> {
    const corrected = Buffer.from(buffer);
    const structure = await this.parseStructure(buffer);
    
    for (const checksum of structure.checksums) {
      const calculated = this.calculateDelphiChecksum(corrected, checksum.start, checksum.end);
      corrected.writeUInt32LE(calculated, checksum.location);
    }

    return corrected;
  }

  private calculateDelphiChecksum(buffer: Buffer, start: number, end: number): number {
    let crc = 0xFFFFFFFF;
    for (let i = start; i < end; i++) {
      crc ^= buffer[i];
      for (let j = 0; j < 8; j++) {
        crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
      }
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }
}