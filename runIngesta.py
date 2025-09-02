import subprocess
import os
import logging
from config import config

logger = logging.getLogger(__name__) 

def validate_table_name(table_name: str) -> None:
    """
    Validate that the table name begins with the configured subenvironment prefix.
    
    Args:
        table_name (str): The table name to validate
        
    Raises:
        ValueError: If table name doesn't begin with the subenvironment prefix
        KeyError: If subenvironment is not configured
    """
    if not table_name:
        raise ValueError("Table name cannot be empty")
    
    try:
        subenvironment = config["validation"]["subenvironment"]
    except KeyError:
        logger.error("Subenvironment validation configuration not found")
        raise KeyError("Subenvironment validation configuration not found")
    
    if not subenvironment:
        logger.error("Subenvironment prefix cannot be empty")
        raise ValueError("Subenvironment prefix cannot be empty")
    
    if not table_name.startswith(subenvironment):
        logger.error(f"Table name '{table_name}' does not start with subenvironment prefix '{subenvironment}'")
        raise ValueError(
            f"Table name '{table_name}' must begin with subenvironment prefix '{subenvironment}'"
        )


def run_redis_ingestion_script(table_name: str) -> int:
    """
    Runs the Redis ingestion script in fire-and-forget mode.
    Starts the script and completely detaches from it, returning immediately.
    
    Args:
        table_name (str): The table name parameter (e.g., 'pr_bsc_3ref.riesgos_calificacion_prestamos_tarjetas_snap')
    
    Returns:
        int: Process ID of the started script
        
    Raises:
        ValueError: If table_name is empty or doesn't match subenvironment prefix
        FileNotFoundError: If the script path or file doesn't exist
        EnvironmentError: If required environment variables are not set
        KeyError: If subenvironment configuration is missing
        
    Example:
        pid = run_redis_ingestion_script("de_table_name")
        print(f"Script started with PID {pid}")
        # Continue with other work - script runs independently
    """
    if not table_name:
        raise ValueError("table_name cannot be empty")
    
    # Validate table name against subenvironment configuration
    validate_table_name(table_name)
    # Get configuration values
    script_path = config["redis_ingestion"]["script_path"]
    script_name = config["redis_ingestion"]["script_name"]
    
    if not script_path:
        logger.error("script_path not found in configuration")
        raise EnvironmentError("script_path not found in configuration")
    
    if not script_name:
        logger.error("script_name not found in configuration")
        raise EnvironmentError("script_name not found in configuration")
    
    if not os.path.exists(script_path):
        logger.error(f"Script path does not exist: {script_path}")
        raise FileNotFoundError(f"Script directory not found: {script_path}")
    
    script_full_path = os.path.join(script_path, script_name)
    if not os.path.exists(script_full_path):
        logger.error(f"Script file not found: {script_full_path}")
        raise FileNotFoundError(f"Script file not found: {script_full_path}")

    command = ["/bin/bash", script_name, "-t", table_name]

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