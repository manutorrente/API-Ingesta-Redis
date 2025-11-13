import subprocess
import os
import logging
from datetime import datetime
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


def run_redis_ingestion_script(table_name: str, notification_email: list[str]) -> dict:
    """
    Runs the Redis ingestion script in fire-and-forget mode.
    Starts the script with proper daemonization and logging.
    
    Args:
        table_name (str): The table name parameter (e.g., 'pr_bsc_3ref.riesgos_calificacion_prestamos_tarjetas_snap')
        notification_email (list[str]): List of email addresses for notifications
    
    Returns:
        dict: Information about the started process
            {
                'pid': int,
                'log_file': str,
                'table_name': str
            }
        
    Raises:
        ValueError: If table_name is empty or doesn't match subenvironment prefix
        FileNotFoundError: If the script path or file doesn't exist
        EnvironmentError: If required environment variables are not set
        KeyError: If subenvironment configuration is missing
        
    Example:
        result = run_redis_ingestion_script("de_table_name", ["user@example.com"])
        print(f"Script started with PID {result['pid']}")
        print(f"Check logs at: {result['log_file']}")
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

    # Build the command
    command = ["/bin/bash", script_name, "-t", table_name]
    
    if notification_email:
        emails_str = " ".join(notification_email)
        command.extend(["--receiver-emails", emails_str])
    
    # Wrap with nohup for proper daemonization
    full_command = ["nohup"] + command
    
    # Create log directory if it doesn't exist
    # Logs will go to: {script_path}/log/execution/{timestamp}_{table_name}.log
    log_dir = os.path.join(script_path, "log", "execution")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a unique log file name with timestamp and sanitized table name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_table_name = table_name.replace(".", "_").replace("/", "_")
    log_filename = f"{timestamp}_{safe_table_name}.log"
    output_log = os.path.join(log_dir, log_filename)
    
    logger.info(f"Running command: {' '.join(full_command)} in {script_path}")
    logger.info(f"Output will be logged to: {output_log}")
    
    # Prepare environment
    env = os.environ.copy()
    env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
    
    # Write execution details to log file header
    with open(output_log, 'w') as log_file:
        log_file.write("=" * 80 + "\n")
        log_file.write(f"Redis Ingestion Process Started\n")
        log_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
        log_file.write(f"Table: {table_name}\n")
        log_file.write(f"Command: {' '.join(full_command)}\n")
        log_file.write(f"Working Directory: {script_path}\n")
        log_file.write(f"Emails: {', '.join(notification_email) if notification_email else 'None'}\n")
        log_file.write("=" * 80 + "\n\n")
        log_file.flush()
        
        # Start the process with proper daemonization
        process = subprocess.Popen(
            full_command,
            cwd=script_path,
            stdout=log_file,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True  # Critical: creates new session, detaches from parent
        )
    
    pid = process.pid
    logger.info(f"Ingestion for table '{table_name}' started with PID {pid}")
    logger.info(f"Monitor progress: tail -f {output_log}")
    
    return {
        'pid': pid,
        'log_file': output_log,
        'table_name': table_name
    }


# Example usage
if __name__ == "__main__":
    # Configure logging for the example
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    table_name = "de_bsc_3ref.motor_comercial_oferta_individuos_snap"
    emails = ["mtorrente@dblandit.com", "manutorrente9@gmail.com"]
    
    try:
        result = run_redis_ingestion_script(table_name, emails)
        print(f"\n{'='*80}")
        print(f"Redis ingestion script started successfully!")
        print(f"{'='*80}")
        print(f"Process ID: {result['pid']}")
        print(f"Table: {result['table_name']}")
        print(f"Log file: {result['log_file']}")
        print(f"\nTo monitor progress, run:")
        print(f"  tail -f {result['log_file']}")
        print(f"\nTo check if process is running:")
        print(f"  ps -p {result['pid']}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"Failed to start script: {e}")
        logger.exception("Failed to start ingestion script")