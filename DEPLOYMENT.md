# Deployment Guide - alwaysdata.com

## Prerequisites
- SSH access to alwaysdata.com server
- Domain: alwaysdata.com (or subdomain like api.alwaysdata.com)
- PostgreSQL database credentials
- Node.js 20+ and Python 3.11+

## Option 1: Docker Deployment (Recommended)

### 1. Prepare Server
```bash
# SSH to server
ssh user@alwaysdata.com

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose
```

### 2. Upload Files
```bash
# On your local machine
cd /path/to/homeworkweb

# Create tarball
tar -czf homeworkweb.tar.gz \
  backend/ \
  frontend/ \
  docker-compose.yml \
  .env.production

# Upload to server
scp homeworkweb.tar.gz user@alwaysdata.com:~/
```

### 3. Setup on Server
```bash
# SSH to server
ssh user@alwaysdata.com

# Extract
tar -xzf homeworkweb.tar.gz
cd homeworkweb

# Copy and configure .env
cp .env.production backend/.env
nano backend/.env  # Edit database URL and other values

# Update docker-compose with your values
nano docker-compose.yml

# Build and start
docker-compose up -d --build
```

### 4. Setup Nginx Reverse Proxy
```bash
sudo nano /etc/nginx/sites-available/homeworkweb
```

Add:
```nginx
# Frontend
server {
    listen 80;
    server_name alwaysdata.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name alwaysdata.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.alwaysdata.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/homeworkweb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Option 2: PM2 Deployment

### 1. Upload Files
```bash
# On local machine
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.venv' \
  backend/ frontend/ ecosystem.config.js \
  user@alwaysdata.com:~/homeworkweb/
```

### 2. Setup Backend
```bash
ssh user@alwaysdata.com
cd homeworkweb/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env
nano .env  # Add your production values

# Initialize database
python scripts/init_db.py
python scripts/seed.py  # Optional
```

### 3. Setup Frontend
```bash
cd ~/homeworkweb/frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Create .env.local
echo "NEXT_PUBLIC_API_URL=https://api.alwaysdata.com/api" > .env.local
```

### 4. Start with PM2
```bash
cd ~/homeworkweb
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 5. Setup Nginx (same as Option 1)

## Environment Variables Checklist

Update these values before deployment:

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection | `postgresql://user:pass@host/db` |
| JWT_SECRET | JWT signing secret | Random long string |
| JWT_REFRESH_SECRET | Refresh token secret | Random long string |
| BOT_TOKEN | Telegram bot token | From BotFather |
| ADMIN_ID | Admin Telegram ID | Your Telegram ID |
| CORS_ORIGINS | Allowed origins | `https://alwaysdata.com` |
| FRONTEND_URL | Frontend URL | `https://alwaysdata.com` |
| BACKEND_URL | Backend URL | `https://api.alwaysdata.com` |

## Troubleshooting

### Check logs
```bash
# Docker
docker-compose logs -f backend
docker-compose logs -f frontend

# PM2
pm2 logs
pm2 logs homeworkweb-backend
pm2 logs homeworkweb-frontend
```

### Restart services
```bash
# Docker
docker-compose restart

# PM2
pm2 restart all
```

### Database migrations
```bash
# Backend directory
source .venv/bin/activate
alembic upgrade head
```
