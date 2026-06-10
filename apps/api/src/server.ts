import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import compress from '@fastify/compress';
import websocket from '@fastify/websocket';
import jwt from '@fastify/jwt';
import swagger from '@fastify/swagger';
import swaggerUI from '@fastify/swagger-ui';
import multipart from '@fastify/multipart';

import { PrismaClient } from '@prisma/client';
import { Redis } from 'ioredis';

const prisma = new PrismaClient();
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379')
});

export async function buildServer() {
  const app = Fastify({
    logger: {
      level: process.env.LOG_LEVEL || 'info',
      serializers: {
        req: (req) => ({
          method: req.method,
          url: req.url,
          hostname: req.hostname
        })
      }
    },
    maxParamLength: 1000,
    bodyLimit: 104857600, // 100MB
    trustProxy: true
  });

  // ============================================
  // PLUGINS
  // ============================================

  // Sécurité
  await app.register(helmet, {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:", "blob:"]
      }
    }
  });

  await app.register(cors, {
    origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
  });

  // Rate limiting
  await app.register(rateLimit, {
    max: 100,
    timeWindow: '1 minute',
    keyGenerator: (request) => {
      return request.headers['x-api-key'] as string || request.ip;
    }
  });

  // Compression
  await app.register(compress, { brotli: true, zstd: true });

  // WebSocket
  await app.register(websocket);

  // JWT
  await app.register(jwt, {
    secret: process.env.JWT_SECRET || 'dev-secret-change-in-production',
    sign: { expiresIn: '24h', algorithm: 'HS512' }
  });

  // Swagger
  await app.register(swagger, {
    openapi: {
      info: {
        title: 'NeuroTune AI API',
        description: 'Professional ECU Calibration Platform API',
        version: '1.0.0'
      },
      servers: [{ url: `http://localhost:${process.env.PORT || 3001}` }],
      components: {
        securitySchemes: {
          bearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' }
        }
      }
    }
  });

  await app.register(swaggerUI, {
    routePrefix: '/docs',
    uiConfig: { docExpansion: 'list', deepLinking: true }
  });

  // Multipart pour uploads
  await app.register(multipart, {
    limits: {
      fileSize: 100 * 1024 * 1024 // 100MB
    }
  });

  // ============================================
  // DECORATORS
  // ============================================

  app.decorate('prisma', prisma);
  app.decorate('redis', redis);

  // ============================================
  // HOOKS
  // ============================================

  // Authentication hook
  app.addHook('onRequest', async (request, reply) => {
    // Skip auth for health check and docs
    if (request.url === '/health' || request.url.startsWith('/docs')) {
      return;
    }

    // Skip auth for public routes
    const publicRoutes = ['/api/auth/login', '/api/auth/register'];
    if (publicRoutes.includes(request.url)) {
      return;
    }

    try {
      await request.jwtVerify();
    } catch (err) {
      reply.status(401).send({ error: 'Unauthorized' });
    }
  });

  // ============================================
  // ROUTES
  // ============================================

  // Health check
  app.get('/health', async () => ({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0'
  }));

  // Auth routes
  app.post('/api/auth/register', async (request, reply) => {
    const { email, password, fullName } = request.body as any;
    
    // Validation simple
    if (!email || !password || !fullName) {
      return reply.status(400).send({ error: 'Missing required fields' });
    }

    // TODO: Implémenter l'enregistrement
    return { message: 'Registration endpoint' };
  });

  app.post('/api/auth/login', async (request, reply) => {
    const { email, password } = request.body as any;
    
    // TODO: Implémenter l'authentification
    const token = app.jwt.sign({ 
      userId: 'test', 
      tenantId: 'test', 
      role: 'tuner' 
    });
    
    return { token };
  });

  // Projects routes
  app.get('/api/projects', async (request, reply) => {
    const { tenantId } = request.user as any;
    
    const projects = await prisma.project.findMany({
      where: { tenantId }
    });
    
    return { data: projects };
  });

  app.post('/api/projects', async (request, reply) => {
    const { tenantId, userId } = request.user as any;
    const { name, description, ecuType } = request.body as any;
    
    const project = await prisma.project.create({
      data: {
        tenantId,
        name,
        description,
        ecuType,
        createdBy: userId
      }
    });
    
    return { data: project };
  });

  // ECU routes
  app.post('/api/ecu/upload', async (request, reply) => {
    const data = await request.file();
    
    if (!data) {
      return reply.status(400).send({ error: 'No file uploaded' });
    }

    const buffer = await data.toBuffer();
    
    // TODO: Traiter le fichier ECU
    return { 
      message: 'File uploaded',
      filename: data.filename,
      size: buffer.length
    };
  });

  app.post('/api/ecu/detect-maps', async (request, reply) => {
    const { fileId } = request.body as any;
    
    // TODO: Appeler le moteur IA pour détecter les maps
    return { message: 'Map detection started', fileId };
  });

  // AI routes
  app.post('/api/ai/analyze', async (request, reply) => {
    const { projectId, analysisTypes } = request.body as any;
    
    // TODO: Appeler le moteur IA
    return { 
      message: 'AI analysis started',
      projectId,
      analysisTypes
    };
  });

  // WebSocket route
  app.get('/ws', { websocket: true }, (socket, req) => {
    socket.on('message', (message: string) => {
      const data = JSON.parse(message);
      
      switch (data.type) {
        case 'subscribe':
          socket.send(JSON.stringify({ 
            type: 'subscribed', 
            channel: data.channel 
          }));
          break;
        default:
          socket.send(JSON.stringify({ 
            type: 'echo', 
            data: data 
          }));
      }
    });

    socket.on('close', () => {
      // Nettoyage
    });
  });

  // ============================================
  // ERROR HANDLERS
  // ============================================

  app.setErrorHandler((error, request, reply) => {
    const statusCode = error.statusCode || 500;
    
    app.log.error({
      err: error,
      request: {
        method: request.method,
        url: request.url
      }
    });

    reply.status(statusCode).send({
      statusCode,
      error: error.name,
      message: error.message,
      timestamp: new Date().toISOString(),
      path: request.url
    });
  });

  app.setNotFoundHandler((request, reply) => {
    reply.status(404).send({
      statusCode: 404,
      error: 'Not Found',
      message: `Route ${request.method} ${request.url} not found`
    });
  });

  return app;
}

// Démarrage
async function start() {
  const app = await buildServer();
  
  try {
    const port = parseInt(process.env.PORT || '3001');
    const host = process.env.HOST || '0.0.0.0';
    
    await app.listen({ port, host });
    console.log(`🚀 NeuroTune API running on http://${host}:${port}`);
    console.log(`📚 Swagger docs: http://${host}:${port}/docs`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

// Gestion de l'arrêt
process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  await prisma.$disconnect();
  await redis.quit();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('Interrupted');
  await prisma.$disconnect();
  await redis.quit();
  process.exit(0);
});

// Démarrer si appelé directement
if (require.main === module) {
  start();
}