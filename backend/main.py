from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import docker
import uuid
import logging
from typing import Dict
import asyncio
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Braien - Browser Container Management API",
             description="API for managing browser containers using Docker",
             version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client
docker_client = docker.from_env()

# Store active containers
active_containers: Dict[str, dict] = {}

# Browser configurations
BROWSER_CONFIGS = {
    "firefox": {
        "image": "jlesage/firefox",
        "ports": {'5800/tcp': None, '5900/tcp': None},
        "web_port": '5800/tcp',
        "environment": {
            'DISPLAY_WIDTH': '1920',
            'DISPLAY_HEIGHT': '1080',
            'VNC_PASSWORD': '',
            'CLEAN_TMP_DIR': '1',
            'FF_OPEN_URL': 'about:blank'
        },
        "startup_delay": 5
    },
    "tor": {
        "image": "domistyle/tor-browser",
        "ports": {'5800/tcp': None},  # Changed from 8080 to 5800
        "web_port": '5800/tcp',
        "environment": {
            'DISPLAY_WIDTH': '1920',
            'DISPLAY_HEIGHT': '1080',
        },
        "docker_args": {
            "shm_size": "2g"  # Add shared memory for Tor browser
        },
        "startup_delay": 10  # Tor needs more time to start
    }
}

def cleanup_container(container_id: str, session_id: str, browser_type: str):
    """Clean up container and associated resources"""
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        
        # Remove the image (optional - you might want to keep it for faster startup)
        # try:
        #     config = BROWSER_CONFIGS.get(browser_type)
        #     if config:
        #         docker_client.images.remove(config["image"], force=True)
        # except Exception as e:
        #     logger.warning(f"Could not remove image: {e}")
            
        # Remove from active containers
        if session_id in active_containers:
            del active_containers[session_id]
            
        logger.info(f"Successfully cleaned up container {container_id}")
    except Exception as e:
        logger.error(f"Error cleaning up container {container_id}: {e}")

def monitor_container(container_id: str, session_id: str, browser_type: str):
    """Monitor container and clean up when it stops"""
    try:
        container = docker_client.containers.get(container_id)
        container.wait()  # Wait for container to stop
        cleanup_container(container_id, session_id, browser_type)
    except Exception as e:
        logger.error(f"Error monitoring container {container_id}: {e}")

@app.post("/launch-browser")
async def launch_browser(browser_data: dict):
    """Launch a browser container"""
    browser_type = browser_data.get("browser", "").lower()
    
    if browser_type not in BROWSER_CONFIGS:
        supported_browsers = list(BROWSER_CONFIGS.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Browser '{browser_type}' not supported. Supported browsers: {supported_browsers}"
        )
    
    try:
        session_id = str(uuid.uuid4())
        config = BROWSER_CONFIGS[browser_type]
        
        # Pull the Docker image
        logger.info(f"Pulling {browser_type} Docker image: {config['image']}...")
        docker_client.images.pull(config["image"])
        
        # Prepare container arguments
        container_args = {
            "image": config["image"],
            "ports": config["ports"],
            "environment": config["environment"],
            "detach": True,
            "remove": False,
            "name": f"{browser_type}-{session_id}"
        }
        
        # Add browser-specific Docker arguments
        if "docker_args" in config:
            container_args.update(config["docker_args"])
        
        # Create and start the container
        logger.info(f"Starting {browser_type} container...")
        container = docker_client.containers.run(**container_args)
        
        # Wait for container to start
        logger.info(f"Waiting for {browser_type} container to initialize...")
        await asyncio.sleep(config.get("startup_delay", 5))
        
        # Get the mapped port
        container.reload()
        web_port = None
        
        # Get the web port mapping
        port_key = config["web_port"]
        port_mappings = container.ports.get(port_key, [])
        
        if port_mappings:
            web_port = port_mappings[0]['HostPort']
        
        if not web_port:
            logger.error(f"Could not get web port for {browser_type}. Available ports: {container.ports}")
            raise HTTPException(status_code=500, detail=f"Could not get web port for {browser_type}")
        
        # Store container info
        active_containers[session_id] = {
            'container_id': container.id,
            'web_port': web_port,
            'browser': browser_type,
            'container_name': container.name
        }
        
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=monitor_container, 
            args=(container.id, session_id, browser_type)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        vnc_url = f"http://localhost:{web_port}"
        logger.info(f"Successfully launched {browser_type} at {vnc_url}")
        
        return {
            "session_id": session_id,
            "vnc_url": vnc_url,
            "status": "running",
            "browser": browser_type,
            "port": web_port
        }
        
    except Exception as e:
        logger.error(f"Error launching {browser_type}: {e}")
        # Clean up any partially created resources
        try:
            if 'container' in locals():
                container.remove(force=True)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to launch {browser_type}: {str(e)}")

@app.delete("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """Manually cleanup a session"""
    if session_id not in active_containers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    container_info = active_containers[session_id]
    cleanup_container(
        container_info['container_id'], 
        session_id, 
        container_info['browser']
    )
    
    return {"message": "Session cleaned up successfully"}

@app.get("/sessions")
async def get_active_sessions():
    """Get all active sessions"""
    return {"active_sessions": list(active_containers.keys())}

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of a specific session"""
    if session_id not in active_containers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    container_info = active_containers[session_id]
    try:
        container = docker_client.containers.get(container_info['container_id'])
        return {
            "session_id": session_id,
            "status": container.status,
            "browser": container_info['browser'],
            "port": container_info['web_port'],
            "vnc_url": f"http://localhost:{container_info['web_port']}"
        }
    except Exception as e:
        return {"session_id": session_id, "status": "error", "error": str(e)}

@app.get("/supported-browsers")
async def get_supported_browsers():
    """Get list of supported browsers"""
    return {"supported_browsers": list(BROWSER_CONFIGS.keys())}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Docker connection
        docker_client.ping()
        return {"status": "healthy", "docker": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "docker": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)