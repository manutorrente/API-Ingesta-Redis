# Redis Ingestion API Service

A FastAPI-based service that provides an HTTP API to trigger Redis ingestion scripts on Linux systems.

## Features

- RESTful API with FastAPI
- Basic authentication with bcrypt password hashing
- Health check endpoint
- Process management for background script execution
- Systemd service integration for Linux

## Prerequisites

- Linux system (Ubuntu 18.04+ or CentOS 7+ recommended)
- Python 3.8 or higher
- Git
- sudo/root access for service installation

## Installation Guide

### Step 1: System Updates and Dependencies

First, update your system and install required packages:

```bash
# For Ubuntu/Debian systems
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# For CentOS/RHEL systems
sudo yum update -y
sudo yum install -y python3 python3-pip git
```

### Step 2: Create Service User

Create a dedicated user for running the service:

```bash
sudo useradd -r -m -s /bin/bash redis-ingestion
sudo usermod -aG sudo redis-ingestion  # Optional: if the service needs sudo access
```

### Step 3: Clone the Repository

Clone the repository to the service user's home directory:

```bash
sudo su - redis-ingestion
cd /home/redis-ingestion
git clone <your-repository-url> redis-ingestion-api
cd redis-ingestion-api
```

### Step 4: Create Python Virtual Environment

Set up a virtual environment for the application:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Step 5: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 6: Environment Configuration

Create and configure the `.env` file:

```bash
cp .env.example .env  # If you have an example file
# OR create a new .env file
nano .env
```

Add the following environment variables to your `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_USERNAME=your_api_username
API_PASSWORD=your_bcrypt_hashed_password

# Script Configuration
SCRIPT_PATH=/path/to/your/redis/scripts
SCRIPT_NAME=your_script_name.sh


```

#### Generating Bcrypt Password Hash

To generate a bcrypt hash for your password, run this Python script:

```bash
python3 -c "
import bcrypt
password = input('Enter password: ')
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print('Hashed password:', hashed.decode('utf-8'))
"
```

Copy the generated hash and use it as the `API_PASSWORD` value in your `.env` file.

### Step 7: Test the Application

Test the application manually to ensure it works:

```bash
# Activate virtual environment
source venv/bin/activate

# Test the application
python main.py
```

In another terminal, test the health endpoint:

```bash
curl http://localhost:8000/health
```

Test the ingestion endpoint (replace credentials and table name):

```bash
curl -u your_username:your_password -X POST \
  "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"table": "your_table_name"}'
```

Stop the test server with `Ctrl+C`.

### Step 8: Create Systemd Service File

Create a systemd service file for the application:

```bash
sudo nano /etc/systemd/system/redis-ingestion-api.service
```

Add the following content:

```ini
[Unit]
Description=Redis Ingestion API Service
After=network.target

[Service]
Type=simple
User=redis-ingestion
Group=redis-ingestion
WorkingDirectory=/home/redis-ingestion/redis-ingestion-api
Environment=PATH=/home/redis-ingestion/redis-ingestion-api/venv/bin
ExecStart=/home/redis-ingestion/redis-ingestion-api/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 9: Configure File Permissions

Set proper permissions for the application files:

```bash
sudo chown -R redis-ingestion:redis-ingestion /home/redis-ingestion/redis-ingestion-api
sudo chmod +x /home/redis-ingestion/redis-ingestion-api/main.py
```

### Step 10: Enable and Start the Service

Enable the service to start on boot and start it:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable redis-ingestion-api

# Start the service
sudo systemctl start redis-ingestion-api
```

## Service Management

### Check Service Status

```bash
sudo systemctl status redis-ingestion-api
```

### View Service Logs

```bash
# View recent logs
sudo journalctl -u redis-ingestion-api -f

# View logs from today
sudo journalctl -u redis-ingestion-api --since today

# View last 100 lines
sudo journalctl -u redis-ingestion-api -n 100
```

### Start the Service

```bash
sudo systemctl start redis-ingestion-api
```

### Stop the Service

```bash
sudo systemctl stop redis-ingestion-api
```

### Restart the Service

```bash
sudo systemctl restart redis-ingestion-api
```

### Disable the Service

```bash
sudo systemctl disable redis-ingestion-api
```

### Reload Service Configuration

After making changes to the service file:

```bash
sudo systemctl daemon-reload
sudo systemctl restart redis-ingestion-api
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Trigger Ingestion

```bash
curl -u username:password -X POST \
  "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"table": "your_table_name"}'
```

## Troubleshooting

### Service Won't Start

1. Check the service status:
   ```bash
   sudo systemctl status redis-ingestion-api
   ```

2. Check the logs:
   ```bash
   sudo journalctl -u redis-ingestion-api -f
   ```

3. Verify file permissions:
   ```bash
   ls -la /home/redis-ingestion/redis-ingestion-api/
   ```

4. Test the application manually:
   ```bash
   sudo su - redis-ingestion
   cd redis-ingestion-api
   source venv/bin/activate
   python main.py
   ```

### Port Already in Use

If port 8000 is already in use, either:

1. Change the port in the `.env` file:
   ```env
   API_PORT=8001
   ```

2. Or find and stop the service using the port:
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

### Authentication Issues

1. Verify the bcrypt hash is correctly generated
2. Ensure the `.env` file has the correct credentials
3. Test with curl using the exact username and password

### Script Execution Issues

1. Verify the `SCRIPT_PATH` and `SCRIPT_NAME` in the `.env` file
2. Ensure the script file exists and is executable:
   ```bash
   ls -la /path/to/your/redis/scripts/
   chmod +x /path/to/your/redis/scripts/your_script_name.sh
   ```

## Security Considerations

1. **Firewall**: Configure firewall rules to restrict access to the API port
2. **HTTPS**: Consider using a reverse proxy (nginx/Apache) with SSL/TLS
3. **Authentication**: Use strong passwords and consider implementing token-based auth
4. **User Permissions**: Run the service with minimal required permissions
5. **Network**: Bind to specific interfaces instead of 0.0.0.0 in production

## File Structure

```
redis-ingestion-api/
├── main.py              # FastAPI application
├── runIngesta.py        # Redis ingestion script runner
├── requirements.txt     # Python dependencies
├── .env                 # Environment configuration
├── .env.example         # Example environment file
└── README.md           # This file
```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_HOST` | Host to bind the API server | No | `0.0.0.0` |
| `API_PORT` | Port for the API server | No | `8000` |
| `API_USERNAME` | Basic auth username | Yes | - |
| `API_PASSWORD` | Bcrypt hashed password | Yes | - |
| `SCRIPT_PATH` | Path to Redis ingestion scripts | Yes | - |
| `SCRIPT_NAME` | Name of the script file | Yes | - |

## Support

For issues and questions, please check the logs first:

```bash
sudo journalctl -u redis-ingestion-api -f
```

Common log locations:
- Service logs: `journalctl -u redis-ingestion-api`
- Application logs: Check the application's log output in the service logs
