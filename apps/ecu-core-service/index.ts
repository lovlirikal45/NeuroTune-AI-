export type ECUResult = {
  size: number;
  endian: "LE" | "BE";
  entropy: number;
  mapCandidates: number;
};

export class ECUCoreService {
  analyze(buffer: Buffer): ECUResult {
    const size = buffer.length;

    // pseudo entropy (base industrielle simplifiée)
    let entropy = 0;
    for (let i = 0; i < buffer.length; i += 1000) {
      entropy += buffer[i] ?? 0;
    }

    return {
      size,
      endian: "LE",
      entropy: entropy % 100,
      mapCandidates: Math.floor(size / 50000)
    };
  }
}