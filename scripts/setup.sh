#!/bin/bash
set -e

echo "🚀 NeuroTune AI - Setup"
echo "========================"

# Vérifier les prérequis
command -v node >/dev/null 2>&1 || { echo "❌ Node.js requis"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "❌ pnpm requis"; exit 1; }

# Installer les dépendances
echo "📦 Installation des dépendances..."
pnpm install

# Copier .env
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
fi

# Docker
if command -v docker >/dev/null 2>&1; then
    echo "🐳 Démarrage des services Docker..."
    docker-compose up -d postgres redis
fi

echo ""
echo "✅ Setup terminé!"
echo "👉 Lancez 'pnpm dev' pour démarrer le développement"
echo "👉 Ou 'docker-compose up -d' pour tout lancer avec Docker"