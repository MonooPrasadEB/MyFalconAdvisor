#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Function to check internet connectivity
check_internet() {
    ping -c 1 api.alpaca.markets > /dev/null 2>&1
    return $?
}

echo -e "${GREEN}Starting Portfolio Sync Service${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo "----------------------------------------"

# Counter for restart attempts
RESTART_COUNT=0
MAX_RESTARTS=3

while true; do
    # Check internet before starting
    if ! check_internet; then
        echo -e "${YELLOW}Waiting for internet connection...${NC}"
        while ! check_internet; do
            sleep 5
        done
        echo -e "${GREEN}Internet connection restored${NC}"
    fi
    
    echo -e "${GREEN}Starting sync service...${NC}"
    # Start the sync service
    python -m myfalconadvisor.tools.portfolio_sync_service
    
    # Increment restart counter
    RESTART_COUNT=$((RESTART_COUNT + 1))
    
    # Check if we've restarted too many times in a row
    if [ $RESTART_COUNT -ge $MAX_RESTARTS ]; then
        echo -e "${RED}Service restarted $MAX_RESTARTS times. Please check for errors.${NC}"
        echo -e "${YELLOW}Waiting 5 minutes before trying again...${NC}"
        sleep 300
        RESTART_COUNT=0
    else
        echo -e "${YELLOW}Service stopped. Restarting in 30 seconds...${NC}"
        sleep 30
    fi
done
