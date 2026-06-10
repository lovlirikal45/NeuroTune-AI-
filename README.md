<div align="center">

![NeuroTune AI](https://img.shields.io/badge/NeuroTune-AI-blue?style=for-the-badge)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-20+-339933?logo=node.js)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?logo=kubernetes)](https://kubernetes.io/)

**Professional AI-Assisted ECU Calibration Platform**

[Documentation](docs/) • [Architecture](docs/architecture/) • [API](docs/api/) • [Contributing](CONTRIBUTING.md)

</div>

---

## 🎯 Vision

NeuroTune AI révolutionne la calibration ECU en combinant l'intelligence artificielle, le calcul haute performance et une interface professionnelle. Notre plateforme permet aux tuners automobiles de travailler plus efficacement avec des outils de nouvelle génération.

## ✨ Fonctionnalités Clés

### 🔍 Détection Automatique de Maps
- **IA avancée**: Réseaux de neurones pour l'identification automatique
- **Multi-formats**: Support BIN, HEX, SREC, A2L, DAMOS
- **Endianess auto**: Détection automatique big/little endian
- **Validation**: Checksums et signatures ECU

### 🧠 Intelligence Artificielle
- **Prédiction AFR**: Optimisation du ratio air/carburant
- **Estimation EGT**: Température des gaz d'échappement
- **Modélisation Couple**: Courbes de couple et puissance
- **Analyse Boost**: Sécurité de suralimentation
- **Suggestions IA**: Recommandations de tuning intelligentes

### 🏎️ Digital Twin
- **Simulation temps réel**: Moteur virtuel complet
- **Visualisation 3D**: WebGL pour l'analyse des maps
- **Replay**: Enregistrement et relecture de sessions
- **Export télémétrie**: Données CAN et ECU

### 🌐 Collaboration Cloud
- **Multi-tenant**: Isolation complète des projets
- **Versioning**: Historique complet des modifications
- **Partage**: Collaboration en temps réel
- **Export**: Formats multiples (BIN, KP, OLS, PDF)

### 🔒 Sécurité Enterprise
- **AES-256-GCM**: Chiffrement des données sensibles
- **RBAC**: Contrôle d'accès granulaire
- **Audit Log**: Traçabilité complète
- **Rate Limiting**: Protection anti-abus
- **Sandbox**: Parsing sécurisé des fichiers

## 🏗️ Architecture Technique

```

┌─────────────────────────────────────────────────────────────┐
│                     NeuroTune AI Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   🖥️ Frontend    │  │  🧠 AI Engine │  │  📊 Analytics  │ │
│  │   React 18       │  │  PyTorch      │  │  Prometheus    │ │
│  │   TypeScript     │  │  ONNX Runtime │  │  Grafana       │ │
│  │   WebGL/Three.js │  │  FastAPI      │  │  OpenTelemetry │ │
│  └─────────────────┘  └──────────────┘  └────────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              ⚙️ Backend API (Fastify/Node.js)              │ │
│  │  ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │ │
│  │  │ ECU Core    │ │Map Engine│ │WinOLS    │ │Security │ │ │
│  │  │ Binary Parse│ │2D/3D Maps│ │KP/OLS    │ │AES/RBAC │ │ │
│  │  └─────────────┘ └──────────┘ └──────────┘ └─────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │            🗄️ Infrastructure (Docker/K8s)                  │ │
│  │  PostgreSQL │ Redis │ MinIO │ BullMQ │ Nginx │           │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

```

## 📦 Modules

| Module | Package | Description | Statut |
|--------|---------|-------------|--------|
| ECU Core | `@neurotune/ecu-core` | Parsing binaire, checksums, plugins ECU | ✅ Production |
| Map Engine | `@neurotune/map-engine` | Détection et manipulation de maps 2D/3D | ✅ Production |
| WinOLS Bridge | `@neurotune/winols-bridge` | Compatibilité KP/OLS | ✅ Production |
| AI Detector | `apps/ai-engine` | Détection IA de maps | ✅ Production |
| AFR Predictor | `apps/ai-engine` | Prédiction ratio air/carburant | ✅ Production |
| EGT Estimator | `apps/ai-engine` | Estimation température échappement | ✅ Production |
| Safety Checker | `apps/ai-engine` | Validation sécurité calibration | ✅ Production |
| Shared Types | `@neurotune/shared-types` | Types TypeScript partagés | ✅ Production |
| UI Components | `@neurotune/ui-components` | Composants React réutilisables | 🚧 Beta |
| CAN Bus | `@neurotune/can-bus` | Utilitaires bus CAN | 📅 Planifié |

## 🚀 Démarrage Rapide

### Prérequis
- **Node.js** ≥ 20.0.0
- **pnpm** ≥ 8.0.0
- **Python** ≥ 3.12
- **Docker** ≥ 24.0.0
- **PostgreSQL** ≥ 15

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/lovlirikal45/NeuroTune-AI-.git
cd NeuroTune-AI-

# 2. Installer les dépendances
pnpm install

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 4. Lancer avec Docker (recommandé)
docker-compose up -d

# 5. Ou lancer en développement
pnpm dev
```

Structure du Projet

```
NeuroTune-AI-/
├── apps/
│   ├── web/                 # Frontend React
│   ├── api/                 # Backend Fastify
│   ├── ai-engine/          # Moteur IA Python
│   ├── parser-service/     # Service de parsing
│   └── simulation-engine/  # Digital Twin
├── packages/
│   ├── ecu-core/           # Core ECU parsing
│   ├── map-engine/         # Détection de maps
│   ├── winols-bridge/      # Compatibilité WinOLS
│   ├── security/           # Utilitaires sécurité
│   ├── shared-types/       # Types partagés
│   └── ui-components/      # Composants React
├── infrastructure/
│   ├── docker/             # Docker Compose
│   ├── kubernetes/         # Manifests K8s
│   └── terraform/          # IaC
├── docs/                   # Documentation
└── scripts/                # Scripts utilitaires
```

🛠️ Stack Technique

Frontend

Technologie Version Usage
React 18.x UI Framework
TypeScript 5.x Langage
Vite 5.x Build Tool
Tailwind CSS 3.x Styling
Zustand 4.x State Management
React Query 5.x Data Fetching
Three.js 160+ 3D Rendering
Monaco Editor 0.45+ Code Editor

Backend

Technologie Version Usage
Node.js 20.x Runtime
Fastify 4.x HTTP Framework
Prisma 5.x ORM
PostgreSQL 15+ Base de données
Redis 7.x Cache/Queue
BullMQ 5.x Job Queue

IA & Machine Learning

Technologie Version Usage
Python 3.12 Runtime
PyTorch 2.x Deep Learning
FastAPI 0.109+ API Framework
ONNX Runtime 1.17+ Inférence
NumPy 1.26+ Calcul numérique
SciPy 1.12+ Optimisation

Infrastructure

Technologie Usage
Docker Conteneurisation
Kubernetes Orchestration
Terraform Infrastructure as Code
Prometheus Monitoring
Grafana Visualisation
OpenTelemetry Tracing

🔒 Sécurité

NeuroTune AI prend la sécurité au sérieux:

· ✅ Chiffrement AES-256-GCM pour toutes les données sensibles
· ✅ JWT avec rotation des clés
· ✅ RBAC avec isolation multi-tenant
· ✅ Audit Logging complet
· ✅ Rate Limiting par IP et API Key
· ✅ Input Validation côté serveur
· ✅ SQL Injection Prevention via Prisma
· ✅ XSS Protection via Content Security Policy
· ✅ CORS configuré strictement
· ✅ Helmet.js pour les headers HTTP sécurisés

📊 Performance

· Parsing de fichiers jusqu'à 500MB en streaming
· Temps de détection < 2 secondes pour fichier 2MB
· Inférence IA < 100ms par prédiction
· Cache Redis avec TTL intelligent
· Compression zstd pour les transferts
· Lazy Loading des modules lourds
· Worker Threads pour le parsing parallèle

🔌 Plugins ECU Supportés

Fabricant Modèles Statut
Bosch ME7.x, MED9.x, MED17.x, EDC16/17 ✅
Siemens MS4x, MSS5x, MSD8x ✅
Delphi MT05, MT35, DCM3.x ✅
Denso SH725xx, R32C ✅
Marelli IAW 4x, 5x, 8x 🚧
Continental SIM2K, EMS3xxx 📅

🤝 Contribution

Les contributions sont les bienvenues! Consultez CONTRIBUTING.md pour les guidelines.

📄 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.
