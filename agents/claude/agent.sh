#!/bin/bash
set -e

echo "=== Motherbrain Claude Agent ==="
echo "Connecting to: $MCP_SERVER_URL"
echo "Channel: $CHANNEL"
echo ""

# Validate required env vars
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    exit 1
fi

if [ -z "$MCP_SERVER_URL" ]; then
    echo "ERROR: MCP_SERVER_URL not set"
    exit 1
fi

# Build MCP server config JSON
MCP_CONFIG=$(cat <<EOF
{
  "motherbrain": {
    "type": "http",
    "url": "$MCP_SERVER_URL",
    "headers": {
      "X-API-Key": "$MCP_API_KEY"
    }
  }
}
EOF
)

# Join the channel first
echo "Joining channel: $CHANNEL"
claude \
    --mcp-server "$MCP_CONFIG" \
    --headless \
    -p "chat_join(sender=\"$AGENT_NAME\", channel=\"$CHANNEL\")"

# If a task was provided, announce it
if [ -n "$TASK" ]; then
    echo "Announcing task: $TASK"
    claude \
        --mcp-server "$MCP_CONFIG" \
        --headless \
        -p "chat_send(sender=\"$AGENT_NAME\", message=\"Starting task: $TASK\", channel=\"$CHANNEL\")"
fi

# Main loop: keep reading chat and responding
echo "Entering main chat loop..."
echo "Press Ctrl+C to exit"
echo ""

LAST_CURSOR=0

while true; do
    # Read messages from channel
    RESPONSE=$(claude \
        --mcp-server "$MCP_CONFIG" \
        --headless \
        -p "chat_read(sender=\"$AGENT_NAME\", channel=\"$CHANNEL\", since_id=$LAST_CURSOR)" 2>/dev/null || echo '{"messages":[],"cursor":0}')
    
    # Parse cursor
    NEW_CURSOR=$(echo "$RESPONSE" | grep -o '"cursor":[0-9]*' | cut -d: -f2 || echo "0")
    if [ -n "$NEW_CURSOR" ] && [ "$NEW_CURSOR" -gt "$LAST_CURSOR" ]; then
        LAST_CURSOR=$NEW_CURSOR
    fi
    
    # Process messages (this is simplified - in production, use jq or proper JSON parsing)
    # For now, we sleep and let claude handle the interaction
    sleep 5
done
