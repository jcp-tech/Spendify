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

# # Authenticate with GCP
# echo "Authenticating with GCP..."
# gcloud auth application-default login

# Deploy ADK pipeline
echo "Deploying ADK pipeline..."
adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service_name=$SERVICE_NAME \
  --app_name=$SERVICE_NAME \
  --port=8080 \
  --log_level=info \
  --with_ui \
  ./receipt_classifier

echo "ADK pipeline deployment script finished."
