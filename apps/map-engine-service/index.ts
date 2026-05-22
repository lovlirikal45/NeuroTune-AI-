export type MapCandidate = {
  address: number;
  confidence: number;
  type: "2D" | "3D";
};

export class MapEngineService {
  detectMaps(buffer: Buffer): MapCandidate[] {
    const maps: MapCandidate[] = [];

    for (let i = 0; i < buffer.length; i += 2048) {
      if (buffer[i] > 50) {
        maps.push({
          address: i,
          confidence: Math.random(),
          type: i % 2 === 0 ? "2D" : "3D"
        });
      }
    }

    return maps;
  }
}