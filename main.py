import os
from typing import Optional
import secrets
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import bcrypt
import logging
from runIngesta import run_redis_ingestion_script
from config import config

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Redis Ingestion API",
    description="API to trigger Redis ingestion scripts",
    version="1.0.0"
)

security = HTTPBasic()

class TableRequest(BaseModel):
    table: str = Field(..., min_length=1, description="Table name for Redis ingestion")

class IngestionResponse(BaseModel):
    success: bool
    message: str
    pid: Optional[int] = None

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic authentication credentials"""
    correct_username = os.getenv("API_USERNAME")
    correct_password = os.getenv("API_PASSWORD")
    
    if not correct_username or not correct_password:
        logger.error("API credentials not found in environment variables")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"), correct_username.encode("utf8")
    )
    try:
        is_correct_password = bcrypt.checkpw(
            credentials.password.encode("utf8"), correct_password.encode("utf8")
        )
    except Exception as e:
        logger.error(f"Bcrypt error: {e}")
        is_correct_password = False
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Redis Ingestion API"}

@app.post("/ingest", response_model=IngestionResponse)
async def trigger_ingestion(
    request: TableRequest,
    username: str = Depends(get_current_user)
):
    """
    Trigger Redis ingestion script for the specified table
    
    Args:
        request: Request body containing the table name
        username: Authenticated username (from basic auth)
    
    Returns:
        IngestionResponse with success status, message, and process ID
    """
    try:
        logger.info(f"User {username} triggering ingestion for table: {request.table}")
        
        pid = run_redis_ingestion_script(request.table)
        
        logger.info(f"Successfully started ingestion script with PID {pid} for table: {request.table}")
        
        return IngestionResponse(
            success=True,
            message=f"Ingestion script started successfully for table '{request.table}'",
            pid=pid
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
        
    except KeyError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server configuration error: {str(e)}"
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script configuration error: {str(e)}"
        )
        
    except EnvironmentError as e:
        logger.error(f"Environment configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Environment configuration error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ingestion script: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    host = config["api"]["host"]
    port = config["api"]["port"]
    
    uvicorn.run(app, host=host, port=port)