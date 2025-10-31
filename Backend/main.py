
"""
DevMindAPI - FastAPI service to bridge with VS Code Copilot Chat
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
import asyncio
import websockets
import json
import logging
import aiosqlite
import sqlite3
import time
import os
from typing import Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevMindAPI",
    description="API to interact with VS Code Copilot Chat",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket configuration for VS Code extension bridge
WS_HOST = "127.0.0.1"  # Use explicit IPv4 address instead of localhost
WS_PORT = 8765
REQUEST_TIMEOUT = 60  # seconds

# Database configuration
DB_PATH = r"Z:\mcp_dashboard.db"
DB_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds

class DatabaseManager:
    """Handles SQLite database operations with better error handling and retry logic"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def execute_with_retry(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False, commit: bool = False):
        """
        Execute SQLite query with retry logic for handling database locks and corruption
        """
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
            try:
                # Check if database file exists and is accessible
                if not os.path.exists(self.db_path):
                    raise FileNotFoundError(f"Database file not found: {self.db_path}")
                
                # Set connection parameters for better network file handling
                async with aiosqlite.connect(
                    self.db_path,
                    timeout=DB_TIMEOUT
                ) as db:
                    # Configure SQLite for better network handling
                    await db.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
                    await db.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
                    await db.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for locks
                    await db.execute("PRAGMA cache_size=10000")  # Larger cache for better performance
                    
                    db.row_factory = aiosqlite.Row
                    
                    # Execute the query
                    cursor = await db.execute(query, params)
                    
                    result = None
                    if fetch_one:
                        result = await cursor.fetchone()
                    elif fetch_all:
                        result = await cursor.fetchall()
                    
                    await cursor.close()
                    
                    if commit:
                        await db.commit()
                    
                    return result
                    
            except sqlite3.DatabaseError as e:
                error_msg = str(e).lower()
                last_exception = e
                
                if "database is locked" in error_msg:
                    logger.warning(f"Database locked on attempt {attempt + 1}/{MAX_RETRIES}, retrying...")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                        continue
                elif "database disk image is malformed" in error_msg:
                    logger.error(f"Database corruption detected: {e}")
                    raise Exception("Database is corrupted. Please contact administrator to restore database.")
                elif "no such table" in error_msg:
                    logger.error(f"Database schema error: {e}")
                    raise Exception("Required database tables not found. Please check database schema.")
                else:
                    logger.error(f"Database error: {e}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
                        continue
                    raise Exception(f"Database error: {str(e)}")
                    
            except FileNotFoundError as e:
                logger.error(f"Database file not found: {e}")
                raise Exception("Database file not accessible. Please check network connection and file permissions.")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected database error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
                raise Exception(f"Database connection failed: {str(e)}")
        
        # If we get here, all retries failed
        raise Exception(f"Database operation failed after {MAX_RETRIES} attempts. Last error: {str(last_exception)}")
    
    async def check_jira_exists(self, jira_id: str) -> bool:
        """Check if JIRA ID exists in the database"""
        try:
            result = await self.execute_with_retry(
                "SELECT 1 FROM jira_dashboard WHERE jira_number = ? LIMIT 1",
                (jira_id,),
                fetch_one=True
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error checking JIRA ID existence: {e}")
            raise
    
    async def get_prompt_template(self, template_key: str = 'analysis_prompt') -> str:
        """Get prompt template from database"""
        try:
            result = await self.execute_with_retry(
                "SELECT p_value FROM jira_prompts_template WHERE p_key = ? LIMIT 1",
                (template_key,),
                fetch_one=True
            )
            if not result or not result["p_value"]:
                raise Exception(f"Prompt template '{template_key}' not found in database")
            return result["p_value"]
        except Exception as e:
            logger.error(f"Error getting prompt template: {e}")
            raise
    
    async def save_prompt(self, jira_id: str, prompt: str) -> bool:
        """Save prompt to jira_tmp_prompts table"""
        try:
            await self.execute_with_retry(
                "INSERT INTO jira_tmp_prompts (jira_no, analysis_prompt) VALUES (?, ?)",
                (jira_id, prompt),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving prompt to database: {e}")
            return False
    
    async def get_all_jira_cards(self) -> list[dict]:
        """Get all JIRA cards from jira_dashboard table with latest jira_prompts data"""
        try:
            result = await self.execute_with_retry(
                """SELECT 
                    jd.id, jd.jira_number, jd.jira_heading, jd.assignee, jd.created, 
                    jd.priority, jd.type, jd.requirement_clarity, jd.automation, 
                    jd.comment, jd.decision, jd.last_updated, jd.status,
                    jp.p_id as prompt_id, jp.category, jp.analysis_prompt, 
                    jp.gen_code, jp.gen_test_case, jp.deployment_prompt, jp.rewards
                   FROM jira_dashboard jd
                   LEFT JOIN (
                       SELECT jp1.*
                       FROM jira_prompts jp1
                       INNER JOIN (
                           SELECT jira_number, MAX(p_id) as max_id
                           FROM jira_prompts
                           GROUP BY jira_number
                       ) jp2 ON jp1.jira_number = jp2.jira_number AND jp1.p_id = jp2.max_id
                   ) jp ON jd.jira_number = jp.jira_number
                   ORDER BY jd.id DESC""",
                fetch_all=True
            )
            
            if result:
                # Convert Row objects to dictionaries and handle BLOB fields
                cards = []
                for row in result:
                    card_data = dict(row)
                    
                    # Convert BLOB fields to strings if they exist
                    blob_fields = ['analysis_prompt', 'gen_code', 'gen_test_case', 'deployment_prompt']
                    for field in blob_fields:
                        if card_data.get(field) is not None:
                            if isinstance(card_data[field], bytes):
                                try:
                                    card_data[field] = card_data[field].decode('utf-8')
                                except UnicodeDecodeError:
                                    card_data[field] = str(card_data[field])
                    
                    cards.append(card_data)
                
                return cards
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting all JIRA cards: {e}")
            raise

# Initialize database manager
db_manager = DatabaseManager(DB_PATH)

class PromptRequest(BaseModel):
    """Request model for Copilot chat prompt"""
    prompt: str = Field(..., min_length=1, description="The prompt to send to Copilot")
    timeout: Optional[int] = Field(default=60, description="Timeout in seconds")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty or whitespace only')
        return v.strip()

class CopilotResponse(BaseModel):
    """Response model from Copilot chat"""
    success: bool
    response: str
    prompt: str
    timestamp: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    bridge_connected: bool
    database_connected: bool
    database_path: str
    timestamp: str

class InjectPromptRequest(BaseModel):
    """Request model for JIRA prompt injection"""
    jira_id: str = Field(..., min_length=1, description="JIRA ID to process")

class InjectPromptResponse(BaseModel):
    """Response model for JIRA prompt injection"""
    isValidJiraId: bool
    isPromptInjectVScode: bool
    genratedPrompt: Optional[str] = None
    error: Optional[str] = None

class JiraCard(BaseModel):
    """Response model for JIRA dashboard card data"""
    id: Optional[int] = Field(None, description="Primary key ID")
    jira_number: str = Field(..., description="JIRA number/ticket ID")
    jira_heading: Optional[str] = Field(None, description="JIRA ticket heading/title")
    assignee: Optional[str] = Field(None, description="Assigned team member")
    created: Optional[str] = Field(None, description="Creation date")
    priority: Optional[str] = Field(None, description="Priority level")
    type: Optional[str] = Field(None, description="JIRA ticket type")
    requirement_clarity: Optional[str] = Field(None, description="Requirement clarity status")
    automation: Optional[str] = Field(None, description="Automation status")
    comment: Optional[str] = Field(None, description="Additional comments")
    decision: Optional[str] = Field("PENDING", description="Decision status")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    status: Optional[str] = Field(None, description="Current status")
    # New fields from jira_prompts table
    prompt_id: Optional[int] = Field(None, description="Prompt primary key ID")
    category: Optional[str] = Field(None, description="Prompt category")
    analysis_prompt: Optional[str] = Field(None, description="Analysis prompt text")
    gen_code: Optional[str] = Field(None, description="Generated code")
    gen_test_case: Optional[str] = Field(None, description="Generated test case")
    deployment_prompt: Optional[str] = Field(None, description="Deployment prompt text")
    rewards: Optional[float] = Field(None, description="Rewards value")

class JiraCardsResponse(BaseModel):
    """Response model for all JIRA cards"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: list[JiraCard] = Field(..., description="List of JIRA cards")
    total_count: int = Field(..., description="Total number of records")
    timestamp: str = Field(..., description="Response timestamp")

# Global WebSocket connection manager
class VSCodeBridgeManager:
    def __init__(self):
        self.ws_client = None
        self.is_connected = False
        self.pending_requests = {}
        
    async def connect(self):
        """Connect to VS Code extension WebSocket server"""
        try:
            self.ws_client = await websockets.connect(f"ws://{WS_HOST}:{WS_PORT}")
            self.is_connected = True
            logger.info(f"Connected to VS Code bridge at ws://{WS_HOST}:{WS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to VS Code bridge: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from VS Code extension"""
        if self.ws_client:
            await self.ws_client.close()
            self.is_connected = False
            logger.info("Disconnected from VS Code bridge")
    
    async def send_prompt(self, prompt: str, timeout: int = 60) -> dict:
        """Send prompt to Copilot via VS Code extension"""
        if not self.is_connected:
            # Try to reconnect
            connected = await self.connect()
            if not connected:
                raise HTTPException(
                    status_code=503,
                    detail="VS Code Copilot bridge is not available. Please ensure the VS Code extension is running."
                )
        
        try:
            # Prepare request
            request_id = datetime.now().isoformat()
            message = {
                "type": "copilot_request",
                "requestId": request_id,
                "prompt": prompt,
                "timestamp": request_id
            }
            
            # Send to VS Code extension
            await self.ws_client.send(json.dumps(message))
            logger.info(f"Sent prompt to VS Code bridge: {prompt[:50]}...")
            
            # Wait for response with timeout
            try:
                response_raw = await asyncio.wait_for(
                    self.ws_client.recv(),
                    timeout=timeout
                )
                response = json.loads(response_raw)
                logger.info(f"Received response from VS Code bridge")
                return response
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for Copilot response")
                raise HTTPException(
                    status_code=504,
                    detail=f"Timeout waiting for Copilot response after {timeout} seconds"
                )
                
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
            logger.error("WebSocket connection closed")
            raise HTTPException(
                status_code=503,
                detail="Connection to VS Code bridge was closed"
            )
        except Exception as e:
            logger.error(f"Error communicating with VS Code bridge: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error communicating with VS Code bridge: {str(e)}"
            )

# Initialize bridge manager
bridge_manager = VSCodeBridgeManager()

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("DevMindAPI starting up...")
    # Try to connect to VS Code bridge (non-blocking)
    try:
        await bridge_manager.connect()
    except Exception as e:
        logger.warning(f"Could not connect to VS Code bridge on startup: {e}")
        logger.info("Will retry on first API request")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("DevMindAPI shutting down...")
    await bridge_manager.disconnect()

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "DevMindAPI - VS Code Copilot Bridge",
        "version": "1.0.0",
        "endpoints": {
            "getCopilotResponseWithVSCodeBridge": "/api/v1/copilot/chat",
            "injectAndSavePrompt": "/api/v1/injectAndSavePrompt",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    database_connected = False
    
    # Test database connectivity
    try:
        # Simple test query to check if database is accessible
        await db_manager.execute_with_retry(
            "SELECT 1 LIMIT 1",
            fetch_one=True
        )
        database_connected = True
        logger.info("Database connectivity test passed")
    except Exception as e:
        logger.warning(f"Database connectivity test failed: {e}")
        database_connected = False
    
    return HealthResponse(
        status="healthy" if database_connected else "degraded",
        bridge_connected=bridge_manager.is_connected,
        database_connected=database_connected,
        database_path=DB_PATH,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/v1/copilot/chat", response_model=CopilotResponse, tags=["Copilot"])
async def getCopilotResponseWithVSCodeBridge(request: PromptRequest):
    """
    Send a prompt to VS Code Copilot Chat and get the response
    
    - **prompt**: The prompt/question to send to Copilot (required, non-empty)
    - **timeout**: Maximum time to wait for response in seconds (default: 60)
    
    Returns the Copilot's response or an error if the bridge is unavailable
    """
    try:
        logger.info(f"Received API request with prompt: {request.prompt[:50]}...")
        
        # Send prompt to VS Code Copilot via bridge
        response = await bridge_manager.send_prompt(
            prompt=request.prompt,
            timeout=request.timeout
        )
        
        # Check if response indicates success
        if response.get("type") == "copilot_response":
            return CopilotResponse(
                success=True,
                response=response.get("response", ""),
                prompt=request.prompt,
                timestamp=datetime.now().isoformat(),
                error=None
            )
        elif response.get("type") == "error":
            return CopilotResponse(
                success=False,
                response="",
                prompt=request.prompt,
                timestamp=datetime.now().isoformat(),
                error=response.get("error", "Unknown error from VS Code bridge")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unexpected response format from VS Code bridge"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v1/injectAndSavePrompt", response_model=InjectPromptResponse, tags=["Jira"])
async def inject_and_save_prompt(request: InjectPromptRequest = Body(...)):
    """
    Validate JIRA ID, generate prompt, inject into Copilot, and save prompt to DB.
    
    - **jira_id**: The JIRA ID to validate and process (required, non-empty)
    
    Returns validation results, injection status, and generated prompt
    """
    jira_id = request.jira_id.strip()
    is_valid_jira = False
    is_prompt_injected = False
    generated_prompt = None

    # 1. Validate JIRA ID
    if not jira_id:
        return InjectPromptResponse(
            isValidJiraId=False, 
            isPromptInjectVScode=False, 
            genratedPrompt=None,
            error="JIRA ID cannot be empty"
        )

    try:
        # 1. Check if JIRA ID exists using database manager
        logger.info(f"Checking JIRA ID existence: {jira_id}")
        is_valid_jira = await db_manager.check_jira_exists(jira_id)
        
        if not is_valid_jira:
            return InjectPromptResponse(
                isValidJiraId=False, 
                isPromptInjectVScode=False, 
                genratedPrompt=None,
                error=f"JIRA ID '{jira_id}' not found in database"
            )

        # 2. Get prompt template using database manager
        logger.info("Getting prompt template from database")
        template_prompt = await db_manager.get_prompt_template('analysis_prompt')

        # 2.ii Replace '?' with JIRA ID
        generated_prompt = template_prompt.replace('?', jira_id)
        logger.info(f"Generated prompt for JIRA {jira_id}")

    except Exception as db_exc:
        error_msg = str(db_exc)
        logger.error(f"Database error in injectAndSavePrompt: {db_exc}")
        
        return InjectPromptResponse(
            isValidJiraId=False, 
            isPromptInjectVScode=False, 
            genratedPrompt=None,
            error=error_msg
        )

    # 3. Inject prompt into Copilot chat (quick check, then fire-and-forget)
    try:
        logger.info("Checking VS Code Copilot bridge connection")
        # Quick connection check
        if not bridge_manager.is_connected:
            connected = await bridge_manager.connect()
            if not connected:
                logger.warning("VS Code Copilot bridge is not available - prompt will be saved to DB only")
                is_prompt_injected = False
            else:
                # Fire and forget - just send the prompt, don't wait for processing
                logger.info("Sending prompt to VS Code Copilot (fire-and-forget)")
                try:
                    await bridge_manager.ws_client.send(json.dumps({
                        "type": "copilot_request",
                        "requestId": datetime.now().isoformat(),
                        "prompt": generated_prompt,
                        "timestamp": datetime.now().isoformat()
                    }))
                    is_prompt_injected = True
                    logger.info("Successfully sent prompt to VS Code Copilot")
                except Exception as send_exc:
                    logger.warning(f"Failed to send prompt: {send_exc}")
                    is_prompt_injected = False
        else:
            # Already connected, just send
            logger.info("Sending prompt to VS Code Copilot")
            try:
                await bridge_manager.ws_client.send(json.dumps({
                    "type": "copilot_request",
                    "requestId": datetime.now().isoformat(),
                    "prompt": generated_prompt,
                    "timestamp": datetime.now().isoformat()
                }))
                is_prompt_injected = True
                logger.info("Successfully sent prompt to VS Code Copilot")
            except Exception as send_exc:
                logger.warning(f"Failed to send prompt: {send_exc}")
                is_prompt_injected = False
    except Exception as copilot_exc:
        logger.warning(f"VS Code Copilot bridge error: {copilot_exc}")
        is_prompt_injected = False

    # 4. Save prompt to jira_tmp_prompts table using database manager
    if is_valid_jira and generated_prompt:
        try:
            logger.info(f"Saving prompt to database for JIRA {jira_id}")
            save_success = await db_manager.save_prompt(jira_id, generated_prompt)
            if save_success:
                logger.info("Successfully saved prompt to database")
            else:
                logger.warning("Failed to save prompt to database")
        except Exception as save_exc:
            logger.error(f"Error saving prompt to database: {save_exc}")

    # 5. Return response
    error_message = None
    if is_valid_jira and not is_prompt_injected:
        error_message = "VS Code Copilot bridge is not available. Prompt saved to database. Please ensure VS Code extension is running on port 8765."
    elif not is_valid_jira:
        error_message = None  # Error already set earlier
    
    return InjectPromptResponse(
        isValidJiraId=is_valid_jira,
        isPromptInjectVScode=is_prompt_injected,
        genratedPrompt=generated_prompt,
        error=error_message
    )

@app.get("/api/v1/jiraCards", response_model=JiraCardsResponse, tags=["Jira"])
async def get_jira_cards():
    """
    Get all JIRA cards from the jira_dashboard table.
    
    Returns:
        JiraCardsResponse: List of all JIRA cards with metadata
    """
    logger.info("Fetching all JIRA cards from database")
    
    try:
        # Get all JIRA cards from database
        jira_cards_data = await db_manager.get_all_jira_cards()
        
        # Convert to Pydantic models
        jira_cards = [JiraCard(**card_data) for card_data in jira_cards_data]
        
        logger.info(f"Successfully retrieved {len(jira_cards)} JIRA cards")
        
        return JiraCardsResponse(
            success=True,
            message=f"Successfully retrieved {len(jira_cards)} JIRA cards",
            data=jira_cards,
            total_count=len(jira_cards),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        error_msg = f"Failed to retrieve JIRA cards: {str(e)}"
        logger.error(error_msg)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database Error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
