export class ECUCore {
  parse(buffer: Buffer) {
    return {
      size: buffer.length,
      endian: "LE",
      maps: []
    }
  }
}
