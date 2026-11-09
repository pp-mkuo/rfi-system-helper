#!/usr/bin/env bash
# Deploy the retrieval service to Cloud Run (source deploy, buildpacks, no Dockerfile).
# Needs: gcloud auth login; PINECONE_API_KEY and RFI_TOKEN in the environment.
set -euo pipefail
: "${PINECONE_API_KEY:?set PINECONE_API_KEY}" "${RFI_TOKEN:?set RFI_TOKEN (any long random string)}"
PROJECT=${GCP_PROJECT:-pp-ai-connectors}   # shared project for Claude-to-data connector services (billing: Ezra, 2026-11)
REGION=${GCP_REGION:-us-east1}
SERVICE=${SERVICE:-rfi-library}
SA="$SERVICE@$PROJECT.iam.gserviceaccount.com"   # dedicated identity with no roles, so the service can reach nothing else in the project
INDEX=${PINECONE_INDEX:-rfi-answer-library}

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iam.googleapis.com --project "$PROJECT" --quiet
gcloud iam service-accounts describe "$SA" --project "$PROJECT" >/dev/null 2>&1 || gcloud iam service-accounts create "$SERVICE" --project "$PROJECT" --display-name "RFI Library retrieval service"
gcloud run deploy "$SERVICE" --source "$(dirname "$0")" --project "$PROJECT" --region "$REGION" \
  --allow-unauthenticated --service-account "$SA" --min-instances 0 --max-instances 3 --memory 256Mi --quiet \
  --set-env-vars "PINECONE_API_KEY=$PINECONE_API_KEY,RFI_TOKEN=$RFI_TOKEN,PINECONE_INDEX=$INDEX"
URL=$(gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format 'value(status.url)')
echo "REST:  POST $URL/search   (header X-RFI-Token)"
echo "MCP:   $URL/mcp/<RFI_TOKEN>   -> add in claude.ai as a custom connector named exactly 'RFI Library'"
