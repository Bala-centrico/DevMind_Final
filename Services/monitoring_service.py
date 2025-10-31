"""
Real-time monitoring service for Jira automation workflow
Provides WebSocket updates on task progress and database changes
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sqlite3
import asyncio
import json
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = r"\\nas3be\ITCrediti\DevMind\mcp_dashboard.db"

app = FastAPI(title="DevMind Monitoring Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models - Define these BEFORE ConnectionManager
class TaskUpdate(BaseModel):
    jira_number: str
    status: str
    stage: str  # analysis, code_generation, testing, deployment
    message: str
    timestamp: str
    progress: int  # 0-100

class ProgressUpdate(BaseModel):
    jiraNumber: str
    stage: str
    status: str  # pending, in-progress, completed, error
    message: str
    progress: int  # 0-100
    timestamp: str

class TaskStatus(BaseModel):
    jira_number: str
    jira_heading: Optional[str]
    status: str
    assignee: Optional[str]
    priority: Optional[str]
    requirement_clarity: Optional[str]
    automation: Optional[str]
    created: Optional[str]
    last_updated: Optional[str]
    decision: Optional[str]
    has_code: bool
    has_test: bool

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Track progress-specific connections by Jira number
        self.progress_connections: Dict[str, set] = {}
        self.progress_cache: Dict[str, ProgressUpdate] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    async def connect_progress(self, websocket: WebSocket, jira_number: str):
        """Connect to progress monitoring for specific Jira"""
        await websocket.accept()
        if jira_number not in self.progress_connections:
            self.progress_connections[jira_number] = set()
        self.progress_connections[jira_number].add(websocket)
        logger.info(f"Progress client connected for {jira_number}")
        
        # Send cached progress if exists
        if jira_number in self.progress_cache:
            await websocket.send_json(self.progress_cache[jira_number].dict())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    def disconnect_progress(self, websocket: WebSocket, jira_number: str):
        """Disconnect from progress monitoring"""
        if jira_number in self.progress_connections:
            self.progress_connections[jira_number].discard(websocket)
            if not self.progress_connections[jira_number]:
                del self.progress_connections[jira_number]
            logger.info(f"Progress client disconnected from {jira_number}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    async def broadcast_progress(self, update: ProgressUpdate):
        """Broadcast progress update to clients monitoring specific Jira"""
        jira_number = update.jiraNumber
        
        # Cache the update
        self.progress_cache[jira_number] = update
        
        # Broadcast to progress-specific clients
        if jira_number in self.progress_connections:
            disconnected = []
            for connection in self.progress_connections[jira_number]:
                try:
                    await connection.send_json(update.dict())
                except Exception as e:
                    logger.error(f"Error sending progress to client: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.progress_connections[jira_number].discard(conn)

manager = ConnectionManager()

# Database monitoring
def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_task_status(jira_number: str) -> Optional[Dict]:
    """Get current status of a Jira task"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                jira_number, jira_heading, status, assignee, priority,
                requirement_clarity, automation, created, last_updated, decision,
                CASE WHEN generated_code_file IS NOT NULL THEN 1 ELSE 0 END as has_code,
                CASE WHEN test_case_file IS NOT NULL THEN 1 ELSE 0 END as has_test,
                comment
            FROM jira_dashboard 
            WHERE jira_number = ?
        """, (jira_number,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def get_all_tasks() -> List[Dict]:
    """Get all tasks from dashboard"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                jira_number, jira_heading, status, assignee, priority,
                requirement_clarity, automation, created, last_updated, decision,
                CASE WHEN generated_code_file IS NOT NULL THEN 1 ELSE 0 END as has_code,
                CASE WHEN test_case_file IS NOT NULL THEN 1 ELSE 0 END as has_test,
                comment
            FROM jira_dashboard 
            ORDER BY last_updated DESC
        """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_jira_prompts(jira_number: str) -> Optional[Dict]:
    """Get prompt details from jira_prompts table"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p_id, jira_number, category, 
                CASE WHEN analysis_prompt IS NOT NULL THEN 1 ELSE 0 END as has_analysis,
                CASE WHEN gen_code IS NOT NULL THEN 1 ELSE 0 END as has_code,
                CASE WHEN gen_test_case IS NOT NULL THEN 1 ELSE 0 END as has_test,
                CASE WHEN deployment_prompt IS NOT NULL THEN 1 ELSE 0 END as has_deployment,
                rewards, created_at
            FROM jira_prompts 
            WHERE jira_number = ?
            ORDER BY p_id DESC
            LIMIT 1
        """, (jira_number,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "DevMind Monitoring Service", "status": "active"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if get_db_connection() else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections)
    }

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks"""
    tasks = get_all_tasks()
    return {"tasks": tasks, "count": len(tasks)}

@app.get("/api/tasks/{jira_number}")
async def get_task(jira_number: str):
    """Get specific task status"""
    task = get_task_status(jira_number)
    if not task:
        return {"error": "Task not found"}, 404
    
    # Also get prompt details if available
    prompts = get_jira_prompts(jira_number)
    
    return {
        "task": task,
        "prompts": prompts,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/tasks/{jira_number}/notify")
async def notify_task_update(jira_number: str, update: TaskUpdate):
    """
    Endpoint for MCP tools to notify about task updates
    This broadcasts updates to all connected WebSocket clients
    """
    logger.info(f"Task update notification: {jira_number} - {update.stage} - {update.message}")
    
    # Broadcast to all WebSocket clients
    await manager.broadcast({
        "type": "task_update",
        "data": update.dict()
    })
    
    return {"status": "broadcasted", "connections": len(manager.active_connections)}

@app.post("/api/progress")
async def receive_progress(update: ProgressUpdate):
    """
    Receive progress updates from VS Code extension
    This is called by the extension as it tracks MCP tool calls
    """
    logger.info(f"Progress update: {update.jiraNumber} - {update.progress}% - {update.message}")
    await manager.broadcast_progress(update)
    return {"status": "broadcasted"}

@app.websocket("/ws/monitor/{jira_number}")
async def websocket_progress_monitor(websocket: WebSocket, jira_number: str):
    """
    WebSocket endpoint for real-time progress monitoring of specific Jira
    Dashboard connects here to receive live progress updates
    """
    await manager.connect_progress(websocket, jira_number)
    try:
        while True:
            # Keep connection alive, wait for messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_progress(websocket, jira_number)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect_progress(websocket, jira_number)

# WebSocket endpoint for real-time monitoring
@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for real-time task monitoring
    Clients connect here to receive live updates
    """
    await manager.connect(websocket)
    
    try:
        # Send initial task list
        tasks = get_all_tasks()
        await websocket.send_json({
            "type": "initial_data",
            "data": tasks,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (like subscription requests)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    jira_number = message.get("jira_number")
                    if jira_number:
                        # Send current status
                        task = get_task_status(jira_number)
                        if task:
                            await websocket.send_json({
                                "type": "task_status",
                                "data": task,
                                "timestamp": datetime.now().isoformat()
                            })
                
                elif message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({
                        "type": "keepalive",
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Database polling task (fallback if MCP tools don't send notifications)
@app.on_event("startup")
async def start_database_monitor():
    """Background task to poll database for changes"""
    asyncio.create_task(poll_database_changes())

async def poll_database_changes():
    """Poll database every 5 seconds for changes and broadcast to clients"""
    last_check_times = {}
    
    while True:
        try:
            await asyncio.sleep(5)  # Poll every 5 seconds
            
            if len(manager.active_connections) == 0:
                continue  # Skip if no clients connected
            
            tasks = get_all_tasks()
            
            for task in tasks:
                jira_number = task['jira_number']
                last_updated = task.get('last_updated', '')
                
                # Check if this task was updated since last check
                if jira_number not in last_check_times or last_check_times[jira_number] != last_updated:
                    last_check_times[jira_number] = last_updated
                    
                    # Broadcast update
                    await manager.broadcast({
                        "type": "task_changed",
                        "data": task,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    logger.info(f"Detected change in task {jira_number}")
                    
        except Exception as e:
            logger.error(f"Error in database polling: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002, log_level="info")
