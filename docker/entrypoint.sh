#!/bin/bash
set -e

# Verify required environment variables are present
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY is not set. Set it in HF Space secrets."
    exit 1
fi

if [ -z "$NEO4J_URI" ]; then
    echo "ERROR: NEO4J_URI is not set. Set it in HF Space secrets."
    exit 1
fi

echo "Starting K8s GraphRAG Chatbot..."
echo "Neo4j: $NEO4J_URI"

exec streamlit run main.py \
    --server.headless=true \
    --server.address=0.0.0.0 \
    --server.port=7860 \
    --server.fileWatcherType=none
