# FreePunch - Open Source Fingerprint Time Clock

Offline-first fingerprint attendance system for headless Debian systems.

## Features

- **Headless Web UI**: FastAPI-based kiosk interface accessible via browser
- **UVC Fingerprint Reader**: Works with any UVC camera device at /dev/video0
- **NBIS Fingerprint Matching**: Industry-standard NIST Biometric Image Software
- **Offline-First**: All data stored locally in SQLite, optional server sync
- **Auto-Toggle**: Intelligent IN/OUT punch detection per user
- **Anti-Bounce**: Prevents duplicate punches within 10 seconds
- **Auto-Punch**: Automatic finger detection and punch triggering
- **Admin Panel**: Employee enrollment, user management, sync control
- **CLI Tools**: Export to CSV, camera testing, user management

## System Requirements

- Debian 11+ (tested on Debian 12)
- Python 3.9+
- UVC-compatible fingerprint reader at /dev/video0
- Minimum 1GB RAM, 4GB storage

## Installation

## Quick Installation
```bash
# Clone repository
git clone https://github.com/ElectronicCats/uvc-fingerprint-server.git /opt/checador
cd /opt/checador

# Run installation script
sudo ./scripts/install_all.sh

# Follow the on-screen instructions
```

## Detailed Installation
### 1. Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    build-essential \
    libopencv-dev python3-opencv \
    v4l-utils sqlite3 \
    libpng-dev libjpeg-dev \
    wget unzip
```

### 2. Install NBIS (NIST Biometric Image Software)

Run script "install_nbis.sh"

### 3. Clone and Install Checador
```bash
# Clone repository
cd /opt
sudo mkdir checador
sudo chown $USER:$USER checador
cd checador

# Copy all project files here
# (or git clone if you have a repo)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Configuration
```bash
# Create directories
sudo mkdir -p /etc/checador
sudo mkdir -p /var/lib/checador/{templates,temp}
sudo chown -R $USER:$USER /var/lib/checador

# Copy example config
cp config.example.toml /etc/checador/config.toml

# Generate admin password hash
python3 -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('admin123'))"

# Edit config and add password hash
nano /etc/checador/config.toml
```

### 5. Camera Calibration (REQUIRED)
```bash
# Start service temporarily
cd /opt/checador
source venv/bin/activate
python3 -m checador.main

# In browser, go to: http://<device-ip>:8000/calibration
# Draw rectangle around fingerprint area
# Click "Save ROI"
# Press Ctrl+C to stop service
```

### 6. Install Systemd Service
```bash
# Copy service file
sudo cp checador.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/checador.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable checador
sudo systemctl start checador
sudo systemctl status checador
```

## Usage

### Web Interface
```
http://<device-ip>:8000         # Main kiosk
http://<device-ip>:8000/admin   # Admin panel
```

### CLI Commands
```bash
# Activate environment
cd /opt/checador
source venv/bin/activate

# Export punches
checador export --output /tmp/punches.csv --start 2025-01-01

# List users
checador users list

# Deactivate user
checador users deactivate --employee-code EMP001

# Test camera
checador camera test

# Manual sync
checador sync now
```

## Troubleshooting

### NBIS Not Found
```bash
# Check installation
which mindtct
which bozorth3

# If not found, add to PATH
export PATH=$PATH:/usr/local/nbis/bin

# Or reinstall NBIS
```

### Camera Issues
```bash
# Check camera device
ls -l /dev/video0
v4l2-ctl --list-devices

# Test with Python
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Service Won't Start
```bash
# Check logs
sudo journalctl -u checador -n 100 --no-pager

# Run manually to see errors
cd /opt/checador
source venv/bin/activate
python3 -m checador.main
```

## Configuration

Edit `/etc/checador/config.toml`:
```toml
[app]
# Application settings
device_id = "CHECADOR-001"
host = "0.0.0.0"
port = 8000
admin_password_hash = "$argon2id$v=19$m=65536,t=3,p=4$..."

[camera]
# Camera settings
device = "/dev/video0"
resolution_width = 640
resolution_height = 480
roi_x = 0
roi_y = 0
roi_width = 640
roi_height = 480

[fingerprint]
# Fingerprint matching settings
mindtct_path = "/usr/local/nbis/bin/mindtct"
bozorth3_path = "/usr/local/nbis/bin/bozorth3"
match_threshold = 40
min_quality_score = 20
required_templates = 3

[database]
# Database settings
path = "/var/lib/checador/checador.db"

[storage]
# Storage paths
template_dir = "/var/lib/checador/templates"
temp_dir = "/var/lib/checador/temp"

[timeclock]
# Time clock settings
antibounce_seconds = 10

[server]
# Server sync settings
enabled = false
url = "https://your-server.com/api"
api_key = "your-api-key"
sync_interval_minutes = 5

[autopunch]
# Auto-punch settings
enabled_on_startup = false
cooldown_seconds = 5
difference_threshold = 0.15
stable_frames = 3
```

## Server API Protocol

POST to `{server.url}/punches`:
```json
{
  "device_id": "CHECADOR-001",
  "punches": [{
    "employee_code": "EMP001",
    "timestamp_utc": "2025-01-15T14:30:00Z",
    "timestamp_local": "2025-01-15T08:30:00-06:00",
    "punch_type": "IN",
    "match_score": 145
  }]
}
```

Expected response: `{"success": true}`

## License

MIT License
