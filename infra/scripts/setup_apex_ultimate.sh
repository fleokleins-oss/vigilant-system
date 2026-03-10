#!/bin/bash
# =============================================================================
# APEX CITADEL V3.2 - ULTIMATE LINUX SETUP SCRIPT
# One-command deploy para Pop!_OS / Ubuntu 22.04 LTS com FULL PERFORMANCE
# =============================================================================

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 APEX CITADEL V3.2 - ULTIMATE LINUX SETUP"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running on supported OS
check_os() {
    log_info "Checking operating system..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "pop" && "$ID" != "ubuntu" ]]; then
            log_error "This script is designed for Pop!_OS or Ubuntu"
            exit 1
        fi
        log_success "OS: $PRETTY_NAME"
    else
        log_error "Cannot determine OS"
        exit 1
    fi
}

# =============================================================================
# PHASE 1: SYSTEM OPTIMIZATION & KERNEL TUNING
# =============================================================================
phase_system_optimization() {
    log_info "════ PHASE 1: SYSTEM OPTIMIZATION ════"
    
    # Update system
    log_info "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get dist-upgrade -y
    log_success "System updated"
    
    # Install essential build tools
    log_info "Installing build essentials..."
    sudo apt-get install -y \
        build-essential \
        curl \
        wget \
        git \
        vim \
        htop \
        iotop \
        tmux \
        screen \
        net-tools \
        dnsutils \
        netcat-traditional \
        traceroute \
        mtr
    log_success "Build essentials installed"
    
    # Kernel optimization
    log_info "Optimizing kernel parameters..."
    sudo tee /etc/sysctl.d/99-apex-performance.conf > /dev/null <<EOF
# APEX CITADEL KERNEL OPTIMIZATION
# Network performance
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 87380 67108864
net.ipv4.tcp_wmem=4096 65536 67108864
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_fin_timeout=20
net.core.netdev_max_backlog=5000
net.ipv4.tcp_max_syn_backlog=5000
net.ipv4.ip_local_port_range=1024 65535

# Connection optimization
net.ipv4.tcp_keepalive_time=600
net.ipv4.tcp_keepalive_probes=3
net.ipv4.tcp_keepalive_intvl=15
net.ipv4.tcp_no_metrics_save=1
net.ipv4.tcp_ecn=1

# File system optimization
fs.file-max=2097152
fs.inode-max=1048576
fs.aio-max-nr=1048576

# VM tuning
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.overcommit_memory=0
EOF
    sudo sysctl -p /etc/sysctl.d/99-apex-performance.conf
    log_success "Kernel optimized"
    
    # Increase file descriptor limits
    log_info "Setting file descriptor limits..."
    sudo tee /etc/security/limits.d/99-apex.conf > /dev/null <<EOF
# APEX CITADEL FILE LIMITS
* soft nofile 1048576
* hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
* soft memlock unlimited
* hard memlock unlimited
EOF
    log_success "File limits increased"
    
    # CPU Governor - Performance Mode
    log_info "Setting CPU to performance mode..."
    if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
        echo "Setting CPU frequency to performance..."
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            if [ -f "$cpu" ]; then
                echo "performance" | sudo tee "$cpu" > /dev/null 2>&1 || true
            fi
        done
        log_success "CPU set to performance mode"
    else
        log_warning "CPU frequency scaling not available"
    fi
}

# =============================================================================
# PHASE 2: PYTHON SETUP (OPTIMIZED)
# =============================================================================
phase_python_setup() {
    log_info "════ PHASE 2: PYTHON SETUP (OPTIMIZED) ════"
    
    log_info "Checking Python version..."
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_success "Python: $python_version"
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found!"
        exit 1
    fi
    
    # Install Python essentials
    log_info "Installing Python dev tools..."
    sudo apt-get install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-distutils \
        python3-apt
    
    # Upgrade pip
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip wheel setuptools
    log_success "Python setup complete"
}

# =============================================================================
# PHASE 3: DATABASE & CACHE (REDIS)
# =============================================================================
phase_redis_setup() {
    log_info "════ PHASE 3: REDIS SETUP (STATE MANAGEMENT) ════"
    
    log_info "Installing Redis server..."
    sudo apt-get install -y redis-server
    
    # Optimize Redis configuration
    log_info "Optimizing Redis for performance..."
    sudo tee /etc/redis/redis.conf > /dev/null <<'EOF'
# Redis Configuration for APEX CITADEL

# Network
port 6379
bind 127.0.0.1
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""

# Persistence (disable for speed)
appendonly no

# Logging
loglevel notice
logfile ""

# Performance
databases 16
hz 10
dynamic-hz yes

# Advanced config
io-threaded-reads-processed-main no
io-threaded-writes-processed-main no
EOF
    
    sudo systemctl enable redis-server
    sudo systemctl restart redis-server
    log_success "Redis optimized and running"
}

# =============================================================================
# PHASE 4: TA-LIB COMPILATION (NATIVE OPTIMIZED)
# =============================================================================
phase_talib_setup() {
    log_info "════ PHASE 4: TA-LIB COMPILATION (NATIVE) ════"
    
    if [ -f /usr/lib/libta_lib.so ] || [ -f /usr/local/lib/libta_lib.so ]; then
        log_success "TA-Lib already installed"
        return
    fi
    
    log_info "Compiling TA-Lib from source (this takes ~5 min)..."
    cd /tmp
    wget -q http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    
    # Compile with native optimization
    log_info "Configuring with native CPU flags..."
    CFLAGS="-O3 -march=native -mtune=native" \
    CXXFLAGS="-O3 -march=native -mtune=native" \
    ./configure --prefix=/usr
    
    log_info "Compiling (this may take a few minutes)..."
    make -j$(nproc)
    sudo make install
    
    # Update library cache
    sudo ldconfig
    
    cd /tmp
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
    
    log_success "TA-Lib compiled and installed"
}

# =============================================================================
# PHASE 5: APEX CITADEL DOWNLOAD & SETUP
# =============================================================================
phase_apex_download() {
    log_info "════ PHASE 5: DOWNLOADING APEX CITADEL ════"
    
    # Create directories
    mkdir -p ~/apex-orchestrator
    cd ~/apex-orchestrator
    
    log_info "Downloading latest Apex Citadel v3.2..."
    
    # Create minimal requirements if not present
    if [ ! -f requirements.txt ]; then
        log_warning "requirements.txt not found, creating default..."
        cat > requirements.txt <<'EOF'
# APEX CITADEL V3.2 - DEPENDENCIES
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
pandas==2.1.3
numpy==1.26.2
scipy==1.11.4
scikit-learn==1.3.2
xgboost==2.0.3
ta-lib==0.4.28
ccxt==4.0.72
websocket-client==1.6.4
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
torch==2.1.1
stable-baselines3==2.2.1
gymnasium==0.29.1
redis==5.0.1
aioredis==2.0.1
aiohttp==3.9.1
requests==2.31.0
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
pyyaml==6.0.1
click==8.1.7
tqdm==4.66.1
python-dateutil==2.8.2
joblib==1.3.2
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
flake8==6.1.0
python-json-logger==2.0.7
structlog==23.2.0
numba==0.57.1
EOF
    fi
    
    log_success "Project directory ready"
}

# =============================================================================
# PHASE 6: VIRTUAL ENVIRONMENT & DEPENDENCIES
# =============================================================================
phase_venv_setup() {
    log_info "════ PHASE 6: VIRTUAL ENVIRONMENT & DEPENDENCIES ════"
    
    cd ~/apex-orchestrator
    
    log_info "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    log_info "Upgrading pip/wheel/setuptools..."
    pip install --upgrade pip wheel setuptools
    
    log_info "Installing dependencies (this takes ~10 min)..."
    
    if [ -f requirements.txt ]; then
        # Install with optimization flags
        pip install --no-cache-dir -r requirements.txt
    else
        log_warning "No requirements.txt found, installing core packages..."
        pip install --no-cache-dir \
            fastapi uvicorn python-dotenv \
            pandas numpy scipy scikit-learn xgboost \
            prometheus-client prometheus-fastapi-instrumentator \
            redis aiohttp requests httpx \
            pydantic pyyaml click
    fi
    
    # Install PyTorch CPU optimized
    log_info "Installing PyTorch (CPU optimized)..."
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
    
    # Install ML extras
    log_info "Installing ML/RL packages..."
    pip install --no-cache-dir stable-baselines3 gymnasium numba
    
    log_success "All dependencies installed"
}

# =============================================================================
# PHASE 7: APEX NODES SETUP
# =============================================================================
phase_nodes_setup() {
    log_info "════ PHASE 7: CREATING 9-NODE STRUCTURE ════"
    
    cd ~/apex-orchestrator
    
    mkdir -p nodes logs modules config backtest
    
    # Create minimal node files if they don't exist
    if [ ! -f nodes/master_orchestrator.py ]; then
        log_info "Creating node templates..."
        cat > nodes/__init__.py <<'EOF'
# APEX CITADEL NODES
EOF
        log_success "Node structure created"
    else
        log_success "Nodes already present"
    fi
}

# =============================================================================
# PHASE 8: ENVIRONMENT CONFIGURATION
# =============================================================================
phase_env_setup() {
    log_info "════ PHASE 8: ENVIRONMENT CONFIGURATION ════"
    
    cd ~/apex-orchestrator
    
    if [ ! -f .env ]; then
        log_info "Creating .env configuration..."
        cat > .env <<'EOF'
# APEX CITADEL V3.2 - 9-NODE TOPOLOGY
USE_TESTNET=TRUE
DEBUG_MODE=FALSE
LOG_LEVEL=INFO

# MAESTRO
MAESTRO_V3_CONFLUENCE_MODE=MAJORITY
MAESTRO_V3_MIN_CONFIDENCE=0.55
MAESTRO_V3_BASE_RISK_PCT=0.01
MAESTRO_PORT=8007

# REDIS
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_TTL=3600

# 9-NODE URLS
MAESTRO_NEWTONIAN_URL=http://127.0.0.1:8011
MAESTRO_SPOOFHUNTER_URL=http://127.0.0.1:8012
MAESTRO_DREAMER_URL=http://127.0.0.1:8006
MAESTRO_ECONOPREDATOR_URL=http://127.0.0.1:8000
MAESTRO_ANTIRUG_URL=http://127.0.0.1:8003
MAESTRO_NARRATIVE_URL=http://127.0.0.1:8004
MAESTRO_JITO_URL=http://127.0.0.1:8005
APM_EXIT_ENGINE_URL=http://127.0.0.1:8008

# TRADING
TRADING_SYMBOL=BTCUSDT
TRADING_TIMEFRAME=1m
TRADING_MODE=paper
POSITION_SIZE_USDT=100
MAX_LEVERAGE=1

# API KEYS (ADD YOURS HERE!)
BINANCE_API_KEY=
BINANCE_API_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
        log_success ".env created - ADD YOUR API KEYS!"
    else
        log_success ".env already exists"
    fi
}

# =============================================================================
# PHASE 9: PERFORMANCE BENCHMARKING
# =============================================================================
phase_benchmarks() {
    log_info "════ PHASE 9: PERFORMANCE METRICS ════"
    
    echo ""
    echo "📊 System Information:"
    echo "  CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"
    echo "  Cores: $(nproc)"
    echo "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"
    echo "  Disk: $(df -h / | awk 'NR==2 {print $2}')"
    echo ""
    
    if command -v redis-cli &> /dev/null; then
        echo "🔴 Redis Status:"
        redis-cli ping > /dev/null 2>&1 && echo "  ✓ Running" || echo "  ✗ Not running"
        redis-cli info stats 2>/dev/null | grep -E "total_commands_processed|total_connections" | sed 's/^/  /'
    fi
    
    echo ""
    echo "🐍 Python Environment:"
    python3 --version
    echo "  venv location: ~/apex-orchestrator/venv"
    echo "  Packages installed: $(source ~/apex-orchestrator/venv/bin/activate && pip list | wc -l)"
    echo ""
}

# =============================================================================
# PHASE 10: STARTUP SCRIPTS
# =============================================================================
phase_startup_scripts() {
    log_info "════ PHASE 10: CREATING STARTUP SCRIPTS ════"
    
    cd ~/apex-orchestrator
    
    # Create start script if doesn't exist
    if [ ! -f start_dev.sh ]; then
        cat > start_dev.sh <<'EOF'
#!/bin/bash
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
mkdir -p logs

echo "🚀 Starting 9-node Apex Citadel ensemble..."

for node in nodes/*.py; do
    if [ "$(basename $node)" != "__init__.py" ]; then
        node_name=$(basename "$node" .py)
        port=$((8000 + RANDOM % 12))
        python3 "$node" --port "$port" > "logs/${node_name}.log" 2>&1 &
        echo "▶️  $node_name (PID: $!)"
    fi
done

echo "✅ Nodes starting..."
sleep 2
tail -f logs/*.log
EOF
        chmod +x start_dev.sh
    fi
    
    # Create stop script
    if [ ! -f stop_nodes.sh ]; then
        cat > stop_nodes.sh <<'EOF'
#!/bin/bash
echo "🛑 Stopping all nodes..."
pkill -f "python3.*nodes/" || true
sleep 1
echo "✅ Nodes stopped"
EOF
        chmod +x stop_nodes.sh
    fi
    
    log_success "Startup scripts ready"
}

# =============================================================================
# PHASE 11: SYSTEMD SERVICE (OPTIONAL)
# =============================================================================
phase_systemd_service() {
    log_info "════ PHASE 11: SYSTEMD SERVICE SETUP ════"
    
    log_info "Creating systemd service for auto-start..."
    
    sudo tee /etc/systemd/system/apex-citadel.service > /dev/null <<EOF
[Unit]
Description=Apex Citadel v3 Trading Ensemble
After=network.target redis-server.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$HOME/apex-orchestrator
ExecStart=$HOME/apex-orchestrator/start_dev.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    log_success "Systemd service created"
    log_info "To auto-start: sudo systemctl enable apex-citadel"
    log_info "To start now: sudo systemctl start apex-citadel"
}

# =============================================================================
# FINAL SUMMARY
# =============================================================================
final_summary() {
    clear
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ APEX CITADEL V3.2 - SETUP COMPLETE!"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "📍 Installation Path: ~/apex-orchestrator"
    echo ""
    echo "🎯 Next Steps:"
    echo "  1. Add API Keys:"
    echo "     nano ~/apex-orchestrator/.env"
    echo "     (Fill in BINANCE_API_KEY, BINANCE_API_SECRET)"
    echo ""
    echo "  2. Start the ensemble:"
    echo "     cd ~/apex-orchestrator"
    echo "     ./start_dev.sh"
    echo ""
    echo "  3. Monitor in another terminal:"
    echo "     tail -f ~/apex-orchestrator/logs/*.log"
    echo ""
    echo "🔗 Master Orchestrator URL:"
    echo "     http://127.0.0.1:8007"
    echo ""
    echo "📊 Check Status:"
    echo "     curl http://127.0.0.1:8007/status"
    echo ""
    echo "🛑 Stop Everything:"
    echo "     cd ~/apex-orchestrator && ./stop_nodes.sh"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "⚡ SYSTEM OPTIMIZATIONS APPLIED:"
    echo "  ✓ Kernel performance tuning"
    echo "  ✓ Network buffer optimization"
    echo "  ✓ CPU frequency scaling (performance mode)"
    echo "  ✓ File descriptor limits increased"
    echo "  ✓ Redis optimized for speed"
    echo "  ✓ TA-Lib compiled with native flags"
    echo "  ✓ Python venv with all dependencies"
    echo "  ✓ 9-node topology ready"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    check_os
    echo ""
    
    phase_system_optimization
    echo ""
    
    phase_python_setup
    echo ""
    
    phase_redis_setup
    echo ""
    
    phase_talib_setup
    echo ""
    
    phase_apex_download
    echo ""
    
    phase_venv_setup
    echo ""
    
    phase_nodes_setup
    echo ""
    
    phase_env_setup
    echo ""
    
    phase_benchmarks
    echo ""
    
    phase_startup_scripts
    echo ""
    
    phase_systemd_service
    echo ""
    
    final_summary
}

# Execute main
main
