#!/bin/bash

# Replace with your Docker Hub username
DOCKER_USERNAME="dmnihal"

# Version tag
VERSION="1.0.0"

# Build and push API image
docker build -t $DOCKER_USERNAME/url-shortener-api:$VERSION ./api
docker push $DOCKER_USERNAME/url-shortener-api:$VERSION

# Build and push Frontend image
docker build -t $DOCKER_USERNAME/url-shortener-frontend:$VERSION ./frontend
docker push $DOCKER_USERNAME/url-shortener-frontend:$VERSION

# Build and push Analytics image
docker build -t $DOCKER_USERNAME/url-shortener-analytics:$VERSION ./analytics
docker push $DOCKER_USERNAME/url-shortener-analytics:$VERSION

# Build and push Worker image
docker build -t $DOCKER_USERNAME/url-shortener-worker:$VERSION ./worker
docker push $DOCKER_USERNAME/url-shortener-worker:$VERSION

# Tag as latest as well
docker tag $DOCKER_USERNAME/url-shortener-api:$VERSION $DOCKER_USERNAME/url-shortener-api:latest
docker tag $DOCKER_USERNAME/url-shortener-frontend:$VERSION $DOCKER_USERNAME/url-shortener-frontend:latest
docker tag $DOCKER_USERNAME/url-shortener-analytics:$VERSION $DOCKER_USERNAME/url-shortener-analytics:latest
docker tag $DOCKER_USERNAME/url-shortener-worker:$VERSION $DOCKER_USERNAME/url-shortener-worker:latest

# Push latest tags
docker push $DOCKER_USERNAME/url-shortener-api:latest
docker push $DOCKER_USERNAME/url-shortener-frontend:latest
docker push $DOCKER_USERNAME/url-shortener-analytics:latest
docker push $DOCKER_USERNAME/url-shortener-worker:latest

echo "All images built and pushed successfully!" 