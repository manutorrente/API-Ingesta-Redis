import subprocess
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__) 

def run_redis_ingestion_script(table_name: str) -> int:
    """
    Runs the Redis ingestion script in fire-and-forget mode.
    Starts the script and completely detaches from it, returning immediately.
    
    Args:
        table_name (str): The table name parameter (e.g., 'pr_bsc_3ref.riesgos_calificacion_prestamos_tarjetas_snap')
    
    Returns:
        int: Process ID of the started script
        
    Raises:
        ValueError: If table_name is empty
        FileNotFoundError: If the script path or file doesn't exist
        EnvironmentError: If required environment variables are not set
        
    Example:
        pid = run_redis_ingestion_script("pr_bsc_3ref.riesgos_calificacion_prestamos_tarjetas_snap")
        print(f"Script started with PID {pid}")
        # Continue with other work - script runs independently
    """
    if not table_name:
        raise ValueError("table_name cannot be empty")
    
    script_path = os.getenv("SCRIPT_PATH")
    script_name = os.getenv("SCRIPT_NAME")
    
    if not script_path:
        logger.error("SCRIPT_PATH environment variable is not set")
        raise EnvironmentError("SCRIPT_PATH environment variable is not set")
    
    if not script_name:
        logger.error("SCRIPT_NAME environment variable is not set")
        raise EnvironmentError("SCRIPT_NAME environment variable is not set")
    
    if not os.path.exists(script_path):
        logger.error(f"Script path does not exist: {script_path}")
        raise FileNotFoundError(f"Script directory not found: {script_path}")
    
    script_full_path = os.path.join(script_path, script_name)
    if not os.path.exists(script_full_path):
        logger.error(f"Script file not found: {script_full_path}")
        raise FileNotFoundError(f"Script file not found: {script_full_path}")
    
    command = ["bash", script_full_path, "-t", table_name]

    logger.info(f"Running command: {' '.join(command)} in {script_path}")

    # Start process completely detached
    process = subprocess.Popen(
        command,
        cwd=script_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    logger.info(f"Ingestion for table '{table_name}' started with PID {process.pid}")

    return process.pid


# # Example usage
# if __name__ == "__main__":
#     table_name = "pr_bsc_3ref.riesgos_calificacion_prestamos_tarjetas_snap"
    
#     try:
#         pid = run_redis_ingestion_script(table_name)
#         print(f"Redis ingestion script started with PID {pid}")
#         print("Script is running independently in the background")
        
#         # Continue with other work here
#         print("Continuing with other tasks...")
        
#     except Exception as e:
#         print(f"Failed to start script: {e}")