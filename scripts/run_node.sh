#!/bin/bash

# Default values
NODE_DIR=""
IMAGE="hybridization-module"
NETWORK_NAME="bridge"
PORT=""

# Function to show usage instructions
usage() {
  echo "Usage: $0 NODE=config/Alice NETWORK=network_name IMAGE=image_name"
  echo "   or: $0 config/Alice image_name network_name port"
  echo "   or: $0 config/Alice  # Defaults to network 'bridge' and image 'hybridization-module'"
  exit 1
}

# Parse arguments (named or positional)
POSITIONAL_ARGS=()

for ARG in "$@"; do
  case $ARG in
    NODE=*)
      NODE_DIR="${ARG#*=}"
      shift
      ;;
    IMAGE=*)
      IMAGE="${ARG#*=}"
      shift
      ;;
    NETWORK=*)
      NETWORK_NAME="${ARG#*=}"
      shift
      ;;
    PORT=*)
      PORT="${ARG#*=}"
      shift
      ;;
    *)
      POSITIONAL_ARGS+=("$ARG")  # Save positional arguments
      ;;
  esac
done

# Handle positional arguments if named ones aren't provided
if [ -z "$NODE_DIR" ] && [ ${#POSITIONAL_ARGS[@]} -ge 1 ]; then
  NODE_DIR="${POSITIONAL_ARGS[0]}"
fi

if [ ${#POSITIONAL_ARGS[@]} -ge 2 ]; then
  IMAGE="${POSITIONAL_ARGS[1]}"
fi

if [ ${#POSITIONAL_ARGS[@]} -ge 3 ]; then
  NETWORK_NAME="${POSITIONAL_ARGS[2]}"
fi

if [ ${#POSITIONAL_ARGS[@]} -ge 4 ]; then
  PORT="${POSITIONAL_ARGS[3]}"
fi

# Validate NODE_DIR
if [ -z "$NODE_DIR" ]; then
  echo "❌ Error: NODE directory is required."
  usage
fi

# Check if the provided directory exists
if [ ! -d "$NODE_DIR" ]; then
  echo "❌ Error: Directory '$NODE_DIR' does not exist."
  exit 1
fi

# Read the UUID from config.json
UUID=$(jq -r '.local_node.uuid' "${NODE_DIR}/config.json")

# Check if UUID was extracted
if [ -z "$UUID" ] || [ "$UUID" == "null" ]; then
  echo "❌ Error: UUID not found in ${NODE_DIR}/config.json"
  exit 1
fi

# Check if PORT was extracted
if [ -z "$PORT" ] || [ "$PORT" == "null" ]; then
  echo "❌ Error: PORT not defined"
  exit 1
fi

# Check if the Docker network exists, create if it doesn't
if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "⚠️  Network '$NETWORK_NAME' does not exist. Creating it..."
  docker network create "$NETWORK_NAME"
fi

# Run the container with the UUID as both the container name and NODE_NAME
docker run -it --name "$UUID" --network "$NETWORK_NAME" \
-p "$PORT":8000 \
-e NODE_NAME="$UUID" \
-v "$(pwd)/${NODE_DIR}/config.json:/app/config.json" \
-v "$(pwd)/${NODE_DIR}/open_connect_request.json:/app/open_connect_request.json" \
"$IMAGE"
