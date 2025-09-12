#!/bin/bash

#### IMPORTANT ####
# This script can only be run from the root of the project.
# DO NOT RUN IT FROM THE scripts/ DIRECTORY

SESSION="kdfix-all"
DOCKER_COMPOSE_DIR="./tests"

# List of container names and python3 commands for 8 panes (adjust as needed)
CONTAINERS=(
  "hm_node_a"
  "hm_node_b"
  "hm_node_b"
  "hm_node_a"
  "hm_node_b"
  "hm_node_c"
  "hm_node_c"
  "hm_node_b"
)
  REQUESTS=(
  "open_connect_request.json"
  "open_connect_request.json"
  "SPI_4_bbbbb_aaaaa_open_connect_request.json"
  "SPI_4_bbbbb_aaaaa_open_connect_request.json"
  "SPI_3_bbbbb_ccccc_open_connect_request.json"
  "SPI_3_bbbbb_ccccc_open_connect_request.json"
  "SPI_5_ccccc_bbbbb__open_connect_request.json"
  "SPI_5_ccccc_bbbbb__open_connect_request.json"
)

# Kill existing session if exists
tmux kill-session -t "$SESSION" 2>/dev/null

# Create tmux session with one big left pane
tmux new-session -d -s "$SESSION" -n nodes "$SHELL"

# Split vertically: left (docker-compose), right (for exec panes)
tmux split-window -h -t "$SESSION:0"
tmux select-pane -t "$SESSION:0.0"
tmux send-keys -t "$SESSION:0.0" "cd $DOCKER_COMPOSE_DIR && docker compose build && docker compose up" C-m

sleep 5

# Now split right pane (index 1) into 8 sub-panes
tmux select-pane -t "$SESSION:0.1"

for i in {1..7}; do
  if [ $((i % 2)) -eq 1 ]; then
    tmux split-window -v -t "$SESSION:0.1"
  else
    tmux split-window -h -t "$SESSION:0.1"
  fi
done

# Layout to tile all 8 on the right
tmux select-layout -t "$SESSION:0" tiled

# Send docker exec commands into each right pane
for i in "${!CONTAINERS[@]}"; do
  sleep 0.5  # ← delay to make sure the pane is ready
  tmux send-keys -t "$SESSION:0.$((i+1))" "docker exec -it ${CONTAINERS[$i]} /bin/bash" C-m
    sleep 0.5
  tmux send-keys -t "$SESSION:0.$((i+1))" "python3 driver.py requests/${REQUESTS[$i]}"
done

# Focus on the docker-compose pane
tmux select-pane -t "$SESSION:0.0"
tmux attach-session -t "$SESSION"
