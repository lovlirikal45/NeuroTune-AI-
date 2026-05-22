export interface ECUFile {
  id: string;
  name: string;
  size: number;
}

export interface MapDTO {
  address: number;
  type: "2D" | "3D";
  confidence: number;
}