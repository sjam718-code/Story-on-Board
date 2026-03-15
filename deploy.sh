#!/bin/bash

# Deploy The Director to Google Cloud Run
# Gemini Live Agent Challenge - Creative Storyteller Category

PROJECT_ID="gen-lang-client-0140832250"
SERVICE_NAME="story-on-board"
REGION="us-central1"

echo "Deploying Story on Board to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

echo ""
echo "Deployment complete!"
echo "Your app should be live at the URL above."
