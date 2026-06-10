import { Buffer } from 'buffer';
import { EcuStructure, EcuIdentification, ParsedMap } from '@neurotune/shared-types';

export interface EcuPlugin {
  readonly manufacturer: string;
  readonly supportedEcus: string[];
  
  identify(buffer: Buffer): Promise<EcuIdentification | null>;
  parseStructure(buffer: Buffer): Promise<EcuStructure>;
  extractMaps(buffer: Buffer, structure: EcuStructure): Promise<ParsedMap[]>;
  validateChecksums(buffer: Buffer): Promise<boolean>;
  correctChecksums(buffer: Buffer): Promise<Buffer>;
}

export abstract class BaseEcuPlugin implements EcuPlugin {
  abstract manufacturer: string;
  abstract supportedEcus: string[];

  protected abstract identificationPatterns: RegExp[];
  protected abstract ecuStructures: Map<string, EcuStructure>;

  async identify(buffer: Buffer): Promise<EcuIdentification | null> {
    const header = buffer.slice(0, 1024).toString('hex');
    
    for (const pattern of this.identificationPatterns) {
      const match = header.match(pattern);
      if (match) {
        return {
          manufacturer: this.manufacturer,
          ecuType: match.groups?.type || 'unknown',
          softwareVersion: match.groups?.version || 'unknown',
          hardwareNumber: match.groups?.hardware || 'unknown'
        };
      }
    }

    return null;
  }

  abstract parseStructure(buffer: Buffer): Promise<EcuStructure>;
  abstract extractMaps(buffer: Buffer, structure: EcuStructure): Promise<ParsedMap[]>;
  abstract validateChecksums(buffer: Buffer): Promise<boolean>;
  abstract correctChecksums(buffer: Buffer): Promise<Buffer>;
}