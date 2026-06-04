#!/bin/bash
set -e

cd "$(dirname "$0")/.."

IMAGE_NAME="ros2_humble_minimal"
DOCKERFILE_PATH="docker/Dockerfile"

echo "Building Dokcer image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" -f "$DOCKERFILE_PATH" .

echo "RUNING CONTAINER..."
docker run -it --rm "$IMAGE_NAME"
