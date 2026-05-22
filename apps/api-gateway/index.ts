import Fastify from "fastify";

const app = Fastify({ logger: true });

app.get("/health", async () => {
  return { status: "ok", service: "api-gateway" };
});

app.post("/ecu/parse", async (req) => {
  const { size } = req.body as any;

  return {
    success: true,
    ecu: {
      size,
      endian: "LE",
      maps: 0
    }
  };
});

app.listen({ port: 3000, host: "0.0.0.0" });