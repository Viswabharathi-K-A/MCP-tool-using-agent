#!/usr/bin/env bash
set -euo pipefail

# CSCI 599 Assignment 1 - build and deploy the MCP agent to Cloud Run.
# Prerequisites: gcloud CLI authenticated, billing enabled, APIs enabled,
# existing Secret Manager secrets, and permission to build/deploy.

PROJECT_ID="csci599-mcp-agent-2026"
REGION="us-west1"
SERVICE="csci599-a1"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE}:latest"

command -v gcloud >/dev/null 2>&1 || { echo "Error: gcloud CLI is not installed." >&2; exit 1; }

# Check that both secrets already exist. Never put API keys in this script.
for secret in openai-api-key tavily-api-key; do
  gcloud secrets describe "$secret" --project "$PROJECT_ID" >/dev/null || {
    echo "Error: Secret Manager secret '$secret' is missing or inaccessible." >&2
    exit 1
  }
done

# Build the Dockerfile in the current project directory and publish the image.
gcloud builds submit . \
  --project "$PROJECT_ID" \
  --tag "$IMAGE"

# Keep the service public, scale to zero when idle, and inject credentials
# from Secret Manager. Existing service account settings are retained.
gcloud run deploy "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --image "$IMAGE" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --memory 1Gi \
  --concurrency 1 \
  --timeout 300 \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,TAVILY_API_KEY=tavily-api-key:latest"

echo "Deployment complete. Cloud Run URL:"
gcloud run services describe "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --format 'value(status.url)'
