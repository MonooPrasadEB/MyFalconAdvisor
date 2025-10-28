#!/bin/bash

# MyFalcon Advisor - Service Stop Script
# Kills all backend and frontend processes

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🦅 MyFalcon Advisor - Stopping Services${NC}"
echo "========================================"

# Kill backend (port 8000)
echo -e "\n${YELLOW}🔪 Stopping backend process (port 8000)...${NC}"
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✅ Backend stopped${NC}"
else
    echo "No backend process found"
fi

# Kill frontend (ports 5173, 5174)
echo -e "${YELLOW}🔪 Stopping frontend process (ports 5173, 5174)...${NC}"
FRONTEND_STOPPED=0
if lsof -ti:5173 > /dev/null 2>&1; then
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    FRONTEND_STOPPED=1
fi
if lsof -ti:5174 > /dev/null 2>&1; then
    lsof -ti:5174 | xargs kill -9 2>/dev/null
    FRONTEND_STOPPED=1
fi

if [ $FRONTEND_STOPPED -eq 1 ]; then
    echo -e "${GREEN}✅ Frontend stopped${NC}"
else
    echo "No frontend process found"
fi

echo ""
echo -e "${GREEN}🎉 All services stopped${NC}"
echo ""

