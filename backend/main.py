"""
Braien - Browser Container Management API

This FastAPI application provides a comprehensive solution for managing browser containers using Docker.
It allows users to launch isolated browser instances (Firefox and Tor) in Docker containers and access
them through VNC web interfaces. The API handles container lifecycle management, monitoring, and cleanup.

Key Features:
- Launch Firefox and Tor browser containers
- VNC web interface access to browsers
- Automatic container monitoring and cleanup
- Session management with unique IDs
- Health checks and status monitoring
- CORS support for frontend integration

Author: Braien Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import docker
import uuid
import logging
from typing import Dict
import asyncio
import threading
import time

# Configure logging to track container operations and errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with metadata
app = FastAPI(title="Braien - Browser Container Management API",
             description="API for managing browser containers using Docker",
             version="1.0.0")

# CORS middleware configuration to allow frontend access
# Enables cross-origin requests from React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Docker client for container management
docker_client = docker.from_env()

# Dictionary to store information about active container sessions
# Key: session_id (UUID), Value: container metadata
active_containers: Dict[str, dict] = {}

# Browser configuration templates defining Docker images, ports, and settings
# Each browser type has specific requirements for VNC access and environment variables
BROWSER_CONFIGS = {
    "firefox": {
        "image": "jlesage/firefox",  # Docker image with Firefox and VNC server
        "ports": {'5800/tcp': None, '5900/tcp': None},  # VNC web and native ports
        "web_port": '5800/tcp',  # Port for web-based VNC access
        "environment": {
            'DISPLAY_WIDTH': '1920',      # Virtual display width
            'DISPLAY_HEIGHT': '1080',     # Virtual display height
            'VNC_PASSWORD': '',           # Empty password for VNC access
            'CLEAN_TMP_DIR': '1',        # Clean temporary files on startup
            'FF_OPEN_URL': 'about:blank' # Default page to open
        },
        "startup_delay": 5  # Seconds to wait for container initialization
    },
    "tor": {
        "image": "domistyle/tor-browser",  # Docker image with Tor browser
        "ports": {'5800/tcp': None},       # VNC web port only
        "web_port": '5800/tcp',            # Port for web-based VNC access
        "environment": {
            'DISPLAY_WIDTH': '1920',   # Virtual display width
            'DISPLAY_HEIGHT': '1080',  # Virtual display height
        },
        "docker_args": {
            "shm_size": "2g"  # Increased shared memory for Tor browser stability
        },
        "startup_delay": 10  # Tor needs more time to establish connections
    }
}

def cleanup_container(container_id: str, session_id: str, browser_type: str):
    """
    Clean up container and associated resources when session ends.
    
    This function handles the complete cleanup process including:
    - Stopping the running container
    - Removing the container from Docker
    - Removing session from active containers tracking
    - Logging cleanup status
    
    Args:
        container_id (str): Docker container ID to cleanup
        session_id (str): Unique session identifier
        browser_type (str): Type of browser (firefox/tor) for logging
    """
    try:
        # Get container object and stop it gracefully
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        
        # Optional: Remove Docker image to save disk space
        # Commented out to improve subsequent launch times
        # try:
        #     config = BROWSER_CONFIGS.get(browser_type)
        #     if config:
        #         docker_client.images.remove(config["image"], force=True)
        # except Exception as e:
        #     logger.warning(f"Could not remove image: {e}")
            
        # Remove session from active containers tracking
        if session_id in active_containers:
            del active_containers[session_id]
            
        logger.info(f"Successfully cleaned up container {container_id}")
    except Exception as e:
        logger.error(f"Error cleaning up container {container_id}: {e}")

def monitor_container(container_id: str, session_id: str, browser_type: str):
    """
    Monitor container lifecycle and trigger cleanup when container stops.
    
    This function runs in a separate thread to watch for container termination
    and automatically clean up resources when the container exits or crashes.
    
    Args:
        container_id (str): Docker container ID to monitor
        session_id (str): Unique session identifier
        browser_type (str): Type of browser for cleanup logging
    """
    try:
        # Get container object and wait for it to stop
        container = docker_client.containers.get(container_id)
        container.wait()  # Blocks until container stops
        
        # Trigger cleanup when container exits
        cleanup_container(container_id, session_id, browser_type)
    except Exception as e:
        logger.error(f"Error monitoring container {container_id}: {e}")

@app.post("/launch-browser")
async def launch_browser(browser_data: dict):
    """
    Launch a new browser container instance.
    
    This endpoint creates and starts a new Docker container with the specified browser,
    configures VNC access, and returns connection details. The process includes:
    1. Validating browser type
    2. Pulling latest Docker image
    3. Creating container with proper configuration
    4. Starting monitoring thread
    5. Returning VNC access URL
    
    Args:
        browser_data (dict): JSON payload containing browser type selection
                           Expected format: {"browser": "firefox"|"tor"}
    
    Returns:
        dict: Session information including VNC URL and session ID
              Format: {
                  "session_id": "uuid",
                  "vnc_url": "http://localhost:port",
                  "status": "running",
                  "browser": "browser_type",
                  "port": "port_number"
              }
    
    Raises:
        HTTPException: 400 if browser type not supported
        HTTPException: 500 if container launch fails
    """
    # Extract and validate browser type from request
    browser_type = browser_data.get("browser", "").lower()
    
    # Check if requested browser is supported
    if browser_type not in BROWSER_CONFIGS:
        supported_browsers = list(BROWSER_CONFIGS.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Browser '{browser_type}' not supported. Supported browsers: {supported_browsers}"
        )
    
    try:
        # Generate unique session identifier
        session_id = str(uuid.uuid4())
        config = BROWSER_CONFIGS[browser_type]
        
        # Pull the latest Docker image to ensure we have updated version
        logger.info(f"Pulling {browser_type} Docker image: {config['image']}...")
        docker_client.images.pull(config["image"])
        
        # Prepare container creation arguments from configuration
        container_args = {
            "image": config["image"],
            "ports": config["ports"],          # Port mappings for VNC access
            "environment": config["environment"], # Environment variables
            "detach": True,                    # Run container in background
            "remove": False,                   # Don't auto-remove on stop
            "name": f"{browser_type}-{session_id}"  # Unique container name
        }
        
        # Add browser-specific Docker arguments (e.g., shared memory for Tor)
        if "docker_args" in config:
            container_args.update(config["docker_args"])
        
        # Create and start the container
        logger.info(f"Starting {browser_type} container...")
        container = docker_client.containers.run(**container_args)
        
        # Wait for container services to initialize properly
        logger.info(f"Waiting for {browser_type} container to initialize...")
        await asyncio.sleep(config.get("startup_delay", 5))
        
        # Refresh container state to get current port mappings
        container.reload()
        web_port = None
        
        # Extract the dynamically assigned host port for VNC web access
        port_key = config["web_port"]
        port_mappings = container.ports.get(port_key, [])
        
        if port_mappings:
            web_port = port_mappings[0]['HostPort']
        
        # Verify that we successfully obtained a port mapping
        if not web_port:
            logger.error(f"Could not get web port for {browser_type}. Available ports: {container.ports}")
            raise HTTPException(status_code=500, detail=f"Could not get web port for {browser_type}")
        
        # Store container information for session management
        active_containers[session_id] = {
            'container_id': container.id,
            'web_port': web_port,
            'browser': browser_type,
            'container_name': container.name
        }
        
        # Start background thread to monitor container lifecycle
        monitor_thread = threading.Thread(
            target=monitor_container, 
            args=(container.id, session_id, browser_type)
        )
        monitor_thread.daemon = True  # Thread dies when main program exits
        monitor_thread.start()
        
        # Construct VNC access URL for frontend
        vnc_url = f"http://localhost:{web_port}"
        logger.info(f"Successfully launched {browser_type} at {vnc_url}")
        
        # Return session details to client
        return {
            "session_id": session_id,
            "vnc_url": vnc_url,
            "status": "running",
            "browser": browser_type,
            "port": web_port
        }
        
    except Exception as e:
        logger.error(f"Error launching {browser_type}: {e}")
        # Clean up any partially created resources on failure
        try:
            if 'container' in locals():
                container.remove(force=True)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to launch {browser_type}: {str(e)}")

@app.delete("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    Manually cleanup a specific browser session.
    
    This endpoint allows clients to explicitly terminate a browser session
    and clean up all associated resources including the Docker container.
    
    Args:
        session_id (str): UUID of the session to cleanup
    
    Returns:
        dict: Confirmation message
    
    Raises:
        HTTPException: 404 if session not found
    """
    # Verify session exists
    if session_id not in active_containers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get container information and trigger cleanup
    container_info = active_containers[session_id]
    cleanup_container(
        container_info['container_id'], 
        session_id, 
        container_info['browser']
    )
    
    return {"message": "Session cleaned up successfully"}

@app.get("/sessions")
async def get_active_sessions():
    """
    Retrieve list of all currently active browser sessions.
    
    This endpoint provides an overview of all running browser containers
    managed by this API instance.
    
    Returns:
        dict: List of active session IDs
              Format: {"active_sessions": ["session_id1", "session_id2", ...]}
    """
    return {"active_sessions": list(active_containers.keys())}

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Get detailed status information for a specific browser session.
    
    This endpoint provides current status, connection details, and metadata
    for a running browser session.
    
    Args:
        session_id (str): UUID of the session to query
    
    Returns:
        dict: Session status details including VNC URL and container status
    
    Raises:
        HTTPException: 404 if session not found
    """
    # Verify session exists
    if session_id not in active_containers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    container_info = active_containers[session_id]
    try:
        # Query current container status from Docker
        container = docker_client.containers.get(container_info['container_id'])
        return {
            "session_id": session_id,
            "status": container.status,
            "browser": container_info['browser'],
            "port": container_info['web_port'],
            "vnc_url": f"http://localhost:{container_info['web_port']}"
        }
    except Exception as e:
        # Return error status if container query fails
        return {"session_id": session_id, "status": "error", "error": str(e)}

@app.get("/supported-browsers")
async def get_supported_browsers():
    """
    Get list of browser types supported by this API.
    
    This endpoint returns all browser configurations available for launching.
    Useful for frontend applications to populate browser selection menus.
    
    Returns:
        dict: List of supported browser names
              Format: {"supported_browsers": ["firefox", "tor", ...]}
    """
    return {"supported_browsers": list(BROWSER_CONFIGS.keys())}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring API and Docker connectivity.
    
    This endpoint verifies that the API is running and can communicate
    with the Docker daemon. Used for service health monitoring and
    load balancer health checks.
    
    Returns:
        dict: Health status and Docker connection state
              Healthy: {"status": "healthy", "docker": "connected"}
              Unhealthy: {"status": "unhealthy", "docker": "disconnected", "error": "..."}
    """
    try:
        # Test Docker daemon connectivity
        docker_client.ping()
        return {"status": "healthy", "docker": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "docker": "disconnected", "error": str(e)}

# Application entry point for direct execution
if __name__ == "__main__":
    """
    Run the FastAPI application using Uvicorn ASGI server.
    
    Configuration:
    - Host: 0.0.0.0 (accept connections from any IP)
    - Port: 8000 (standard development port)
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)