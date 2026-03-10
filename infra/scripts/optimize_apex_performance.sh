#!/bin/bash
# =============================================================================
# APEX CITADEL - POST-SETUP OPTIMIZATION SCRIPT
# Otimizações adicionais para máxima performance
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

echo "════════════════════════════════════════════════════════════════"
echo "🔧 APEX CITADEL - ADVANCED PERFORMANCE OPTIMIZATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# =============================================================================
# 1. DISABLE UNNECESSARY SERVICES
# =============================================================================
log_info "Disabling unnecessary services..."

services_to_disable=(
    "cups"              # Printing
    "avahi-daemon"      # Bonjour
    "bluetooth"         # Bluetooth
    "ModemManager"      # Mobile broadband
    "snapd"             # Snap daemon
)

for service in "${services_to_disable[@]}"; do
    if systemctl is-enabled "$service" 2>/dev/null | grep -q enabled; then
        sudo systemctl disable "$service" 2>/dev/null || true
        sudo systemctl stop "$service" 2>/dev/null || true
        log_success "Disabled $service"
    fi
done

echo ""

# =============================================================================
# 2. ADVANCED NETWORK TUNING
# =============================================================================
log_info "Advanced network performance tuning..."

sudo tee /etc/sysctl.d/99-apex-network-advanced.conf > /dev/null <<'EOF'
# ADVANCED NETWORK OPTIMIZATION FOR APEX

# TCP tuning
net.ipv4.tcp_congestion_control=bbr
net.ipv4.tcp_notsent_lowat=16384
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_max_tw_buckets=2000000
net.ipv4.tcp_abort_on_overflow=0

# UDP tuning
net.core.udp_mem=262144 524288 1048576

# Connection backlog
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535

# Protocol optimization
net.ipv4.icmp_echo_ignore_broadcasts=1
net.ipv4.icmp_ignore_bogus_error_responses=1
net.ipv4.tcp_challenge_ack_limit=2147483647

# Timestamp & SACK (improves performance)
net.ipv4.tcp_timestamps=1
net.ipv4.tcp_sack=1
net.ipv4.tcp_fack=1

# Window scaling
net.ipv4.tcp_window_scaling=1

# SYN cookies
net.ipv4.tcp_syncookies=1
EOF

sudo sysctl -p /etc/sysctl.d/99-apex-network-advanced.conf > /dev/null
log_success "Network tuning applied"

echo ""

# =============================================================================
# 3. DISK I/O OPTIMIZATION
# =============================================================================
log_info "Optimizing disk I/O..."

# Find main disk
MAIN_DISK=$(lsblk -d -o NAME,ROTA | grep 1 | head -1 | awk '{print $1}')

if [ -z "$MAIN_DISK" ]; then
    MAIN_DISK=$(lsblk -d -o NAME | head -1)
fi

if [ ! -z "$MAIN_DISK" ]; then
    echo "Found disk: $MAIN_DISK"
    
    # Set scheduler to mq-deadline (for SSD) or noop
    if [[ $(cat /sys/block/$MAIN_DISK/queue/rotational) == "0" ]]; then
        echo "mq-deadline" | sudo tee /sys/block/$MAIN_DISK/queue/scheduler > /dev/null
        log_success "SSD scheduler optimized (mq-deadline)"
    else
        echo "noop" | sudo tee /sys/block/$MAIN_DISK/queue/scheduler > /dev/null
        log_success "HDD scheduler optimized (noop)"
    fi
    
    # Increase read-ahead
    echo 256 | sudo tee /sys/block/$MAIN_DISK/queue/read_ahead_kb > /dev/null
    log_success "Read-ahead increased"
fi

echo ""

# =============================================================================
# 4. MEMORY & CACHE TUNING
# =============================================================================
log_info "Optimizing memory and cache..."

sudo tee /etc/sysctl.d/99-apex-memory.conf > /dev/null <<'EOF'
# Memory optimization
vm.swappiness=5
vm.dirty_ratio=50
vm.dirty_background_ratio=10
vm.dirty_expire_centisecs=6000
vm.dirty_writeback_centisecs=500

# Page cache
vm.page-cluster=3
vm.readahead_kb=256

# Memory allocation
vm.overcommit_memory=0
vm.overcommit_ratio=50

# Drop cache command (use: echo 3 | sudo tee /proc/sys/vm/drop_caches)
vm.vfs_cache_pressure=100
EOF

sudo sysctl -p /etc/sysctl.d/99-apex-memory.conf > /dev/null
log_success "Memory optimization applied"

echo ""

# =============================================================================
# 5. CPU AFFINITY & ISOLATION
# =============================================================================
log_info "Setting up CPU affinity..."

CORES=$(nproc)
log_success "System has $CORES cores"

# Create cpuset for APEX processes
if [ ! -d "/cpuset/apex" ]; then
    sudo mkdir -p /cpuset/apex 2>/dev/null || true
    log_success "CPUset created"
else
    log_success "CPUset already exists"
fi

echo ""

# =============================================================================
# 6. LIMIT BACKGROUND NOISE
# =============================================================================
log_info "Reducing system background noise..."

# Disable system updates timing
sudo tee /etc/apt/apt.conf.d/99-no-auto-update > /dev/null <<'EOF'
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
EOF

log_success "Auto-updates disabled"

echo ""

# =============================================================================
# 7. ISOLATE CORES FOR APEX (OPTIONAL ADVANCED)
# =============================================================================
log_info "Setting up core isolation (optional)..."

GRUB_CMD="isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3"

if ! grep -q "isolcpus" /etc/default/grub; then
    log_warning "To isolate cores, add this to /etc/default/grub:"
    log_warning "GRUB_CMDLINE_LINUX=\"$GRUB_CMD\""
    log_warning "Then run: sudo update-grub && sudo reboot"
else
    log_success "Core isolation already configured"
fi

echo ""

# =============================================================================
# 8. PYTHON OPTIMIZATION
# =============================================================================
log_info "Python runtime optimization..."

cat > ~/.pythonrc <<'EOF'
import sys
import readline
import rlcompleter

# Enable optimization
sys.flags.optimize = 2

# Increase buffer size
import io
io.DEFAULT_BUFFER_SIZE = 1048576

# Load completer
readline.parse_and_bind("tab: complete")
rlcompleter.Completer().complete
EOF

export PYTHONOPTIMIZE=2
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

log_success "Python optimization configured"

echo ""

# =============================================================================
# 9. REDIS PERSISTENCE TUNING
# =============================================================================
log_info "Fine-tuning Redis..."

sudo tee -a /etc/redis/redis.conf > /dev/null <<'EOF'

# Performance tuning
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
replica-lazy-flush yes
lazyfree-lazy-user-del yes

# RDB compression
rdbcompression no
rdbchecksum no

# AOF disabled (for speed)
appendonly no

# Max memory policy
maxmemory 2gb
maxmemory-policy allkeys-lru

# Disable protected mode
protected-mode no
EOF

sudo systemctl restart redis-server
log_success "Redis optimized"

echo ""

# =============================================================================
# 10. CREATE PERFORMANCE MONITORING SCRIPT
# =============================================================================
log_info "Creating performance monitoring script..."

mkdir -p ~/apex-orchestrator/scripts

cat > ~/apex-orchestrator/scripts/monitor.sh <<'EOF'
#!/bin/bash
# Performance monitoring for APEX

watch -n 1 "
echo '═══════════════════════════════════════'
echo '🎯 APEX CITADEL PERFORMANCE MONITOR'
echo '═══════════════════════════════════════'
echo ''
echo '⚡ CPU:'
echo \"  Load Average: $(uptime | awk -F'load average:' '{print $2}')\"
echo \"  CPU Usage: $(top -bn1 | grep \"Cpu(s)\" | awk '{print \$2}' | cut -d'%' -f1)%\"
echo ''
echo '💾 MEMORY:'
free -h | tail -2
echo ''
echo '🔴 REDIS:'
redis-cli info stats | grep -E 'connected_clients|used_memory_human|total_commands'
echo ''
echo '📊 DISK I/O:'
iostat -x 1 2 | tail -1
echo ''
echo '🔗 APEX NODES:'
for port in 8000 8003 8004 8005 8006 8007 8008 8011 8012; do
    curl -s http://127.0.0.1:\$port/health 2>/dev/null | jq '.node' 2>/dev/null && echo \"  Port \$port: OK\" || echo \"  Port \$port: DOWN\"
done
"
EOF

chmod +x ~/apex-orchestrator/scripts/monitor.sh
log_success "Monitor script created"

echo ""

# =============================================================================
# 11. FINAL RECOMMENDATIONS
# =============================================================================
clear
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ POST-SETUP OPTIMIZATION COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📌 PERFORMANCE ENHANCEMENTS APPLIED:"
echo "  ✓ Unnecessary services disabled"
echo "  ✓ Advanced network tuning (BBR, TCP fast open)"
echo "  ✓ Disk I/O scheduler optimized"
echo "  ✓ Memory and cache tuning"
echo "  ✓ CPU affinity prepared"
echo "  ✓ Background noise reduced"
echo "  ✓ Python runtime optimized"
echo "  ✓ Redis fine-tuned"
echo "  ✓ Performance monitor created"
echo ""
echo "🚀 ADVANCED OPTIONS (Optional, requires reboot):"
echo "  1. CPU Core Isolation:"
echo "     Edit: /etc/default/grub"
echo "     Add: isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3"
echo "     Then: sudo update-grub && sudo reboot"
echo ""
echo "  2. Disable CPU frequency scaling:"
echo "     echo 'powersave' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
echo ""
echo "  3. Increase shared memory:"
echo "     sudo sysctl -w kernel.shmmax=2147483648"
echo ""
echo "📊 MONITORING:"
echo "  Real-time performance: ~/apex-orchestrator/scripts/monitor.sh"
echo "  System stats: htop, iotop, nethogs"
echo ""
echo "🔍 VERIFY OPTIMIZATION:"
echo "  Network: sysctl net.ipv4.tcp_congestion_control"
echo "  Memory: cat /proc/sys/vm/swappiness"
echo "  Redis: redis-cli info stats"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
