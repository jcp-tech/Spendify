#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a
# if [ -f .env ]; then
#   export $(cat .env | sed 's/#.*//g' | xargs)
# fi

# Set active GCP project
echo "Setting active GCP project..."
gcloud config set project $GOOGLE_CLOUD_PROJECT

# # Enable required services
# echo "Enabling required services..."
# gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Build and push Docker image
echo "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME \
  --platform managed \
  --region $GOOGLE_CLOUD_LOCATION \
  --allow-unauthenticated

echo "Flask API deployment script finished."
