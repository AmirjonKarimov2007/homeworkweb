#!/bin/bash

# Deployment script for alwaysdata.com

set -e

# Configuration
SERVER_USER="your_username"
SERVER_HOST="alwaysdata.com"
DEPLOY
_PATH="/var/www/homeworkweb"

echo "🚀 Starting deployment to $SERVER_HOST..."

# Build tarball
echo "📦 Creating deployment package..."
tar -czf homeworkweb-deploy.tar.gz \
  backend/ \
  frontend/ \
  docker-compose.yml \
  .dockerignore \
  --exclude='*/__pycache__' \
  --exclude='*/.venv' \
  --exclude='*/node_modules' \
  --exclude='*/.next' \
  --exclude='*.log'

# Upload to server
echo "📤 Uploading files..."
scp homeworkweb-deploy.tar.gz $SERVER_USER@$SERVER_HOST:/tmp/

# Deploy on server
echo "🔧 Deploying on server..."
ssh $SERVER_USER@$SERVER_HOST << 'ENDSSH'
set -e

echo "Stopping existing services..."
cd $DEPLOY_PATH || mkdir -p $DEPLOY_PATH
[ -f docker-compose.yml ] && docker-compose down || true

echo "Extracting new files..."
rm -rf old
mv current old 2>/dev/null || true
mkdir -p current
cd current
tar -xzf /tmp/homeworkweb-deploy.tar.gz
rm /tmp/homeworkweb-deploy.tar.gz

echo "Building and starting containers..."
docker-compose up -d --build

echo "Cleaning up old files..."
rm -rf old

echo "✅ Deployment complete!"
ENDSSH

# Clean up local
rm homeworkweb-deploy.tar.gz

echo "🎉 Deployment finished!"
echo "🌐 Frontend: https://alwaysdata.com"
echo "🔌 Backend:  https://api.alwaysdata.com"
