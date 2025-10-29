#!/bin/bash

# MyFalcon Advisor - Service Startup Script
# Kills existing processes and starts backend + frontend

set -e

PROJECT_DIR="/Users/monooprasad/Documents/MyFalconAdvisorv1"
LOG_DIR="/tmp/falcon"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🦅 MyFalcon Advisor - Starting Services${NC}"
echo "========================================"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Kill existing backend (port 8000)
echo -e "\n${YELLOW}🔪 Killing existing backend process (port 8000)...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No backend process found"

# Kill existing frontend (ports 5173, 5174)
echo -e "${YELLOW}🔪 Killing existing frontend process (ports 5173, 5174)...${NC}"
lsof -ti:5173 | xargs kill -9 2>/dev/null || echo "No frontend on 5173"
lsof -ti:5174 | xargs kill -9 2>/dev/null || echo "No frontend on 5174"

# Wait for ports to be released
echo -e "${YELLOW}⏳ Waiting for ports to be released...${NC}"
sleep 2

# Start backend
echo -e "\n${GREEN}🚀 Starting backend API (port 8000)...${NC}"
cd "$PROJECT_DIR"
# Activate venv and start backend
source venv/bin/activate && python start_web_api.py > "$LOG_DIR/web_api.log" 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to initialize
echo -e "${YELLOW}⏳ Waiting for backend to initialize...${NC}"
sleep 3

# Check if backend is running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running on http://localhost:8000${NC}"
    echo -e "   Logs: tail -f $LOG_DIR/web_api.log"
else
    echo -e "${RED}❌ Backend failed to start. Check logs: cat $LOG_DIR/web_api.log${NC}"
    exit 1
fi

# Start frontend
echo -e "\n${GREEN}🚀 Starting frontend (port 5173)...${NC}"
cd "$PROJECT_DIR"
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to initialize
echo -e "${YELLOW}⏳ Waiting for frontend to initialize...${NC}"
sleep 3

# Check if frontend is running (may use 5173 or 5174)
if lsof -ti:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running on http://localhost:5173${NC}"
    echo -e "   Logs: tail -f $LOG_DIR/frontend.log"
elif lsof -ti:5174 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running on http://localhost:5174${NC}"
    echo -e "   Logs: tail -f $LOG_DIR/frontend.log"
else
    echo -e "${RED}❌ Frontend failed to start. Check logs: cat $LOG_DIR/frontend.log${NC}"
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo "📊 Service URLs:"
echo "   Backend API:  http://localhost:8000"
echo "   Frontend UI:  http://localhost:5173 (or 5174)"
echo "   API Docs:     http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f $LOG_DIR/web_api.log"
echo "   Frontend: tail -f $LOG_DIR/frontend.log"
echo ""
echo "🛑 To stop services:"
echo "   ./stop_services.sh"
echo ""

