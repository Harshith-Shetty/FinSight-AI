#!/bin/bash
# Simple deployment script for FinSight AI EC2 Instance

echo "Pulling latest code from git..."
git pull origin main

echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "Applying Database Migrations..."
# Run the migrations inside a temporary api container
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

echo "Restarting containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "Deployment completed successfully!"
