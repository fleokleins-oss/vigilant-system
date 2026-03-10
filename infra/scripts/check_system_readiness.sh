#!/bin/bash
# =============================================================================
# APEX CITADEL - PRE-SETUP SYSTEM CHECKER
# Validates system readiness before running setup
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

PASS=0
WARN=0
FAIL=0

check_pass() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASS++))
}

check_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARN++))
}

check_fail() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAIL++))
}

check_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

clear
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔍 APEX CITADEL - PRE-SETUP SYSTEM CHECKER"
echo "════════════════════════════════════════════════════════════════"
echo ""

# =============================================================================
# 1. OS CHECK
# =============================================================================
echo "📋 OPERATING SYSTEM"
echo "──────────────────────────────────────"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    
    if [[ "$ID" == "pop" || "$ID" == "ubuntu" ]]; then
        check_pass "OS: $PRETTY_NAME"
        
        MAJOR_VERSION=$(echo $VERSION_ID | cut -d. -f1)
        if [ "$MAJOR_VERSION" -ge 22 ]; then
            check_pass "Ubuntu/Pop!_OS version: $VERSION_ID (22.04+)"
        else
            check_warn "Ubuntu version $VERSION_ID (recommend 22.04+)"
        fi
    else
        check_fail "OS: $PRETTY_NAME (not Ubuntu/Pop!_OS)"
    fi
else
    check_fail "Cannot detect OS"
fi

echo ""

# =============================================================================
# 2. HARDWARE CHECK
# =============================================================================
echo "💻 HARDWARE SPECIFICATIONS"
echo "──────────────────────────────────────"

CPU_CORES=$(nproc)
CPU_MODEL=$(lscpu | grep 'Model name' | cut -d: -f2 | xargs)
RAM_GB=$(free -h | awk '/^Mem:/ {print $2}' | sed 's/G.*//')
DISK_GB=$(df / | awk 'NR==2 {print $4}' | sed 's/G.*//')

check_info "CPU: $CPU_MODEL"
check_info "Cores: $CPU_CORES"
check_info "RAM: ${RAM_GB}GB"
check_info "Disk (Root): ${DISK_GB}GB available"

# Recommendations
if [ "$CPU_CORES" -ge 4 ]; then
    check_pass "CPU cores: $CPU_CORES (4+ recommended)"
else
    check_warn "CPU cores: $CPU_CORES (4+ recommended)"
fi

if [ "${RAM_GB%.*}" -ge 8 ]; then
    check_pass "RAM: ${RAM_GB}GB (8GB+ recommended)"
else
    check_warn "RAM: ${RAM_GB}GB (8GB+ recommended)"
fi

if [ "${DISK_GB%.*}" -ge 50 ]; then
    check_pass "Disk space: ${DISK_GB}GB (50GB+ recommended)"
else
    check_warn "Disk space: ${DISK_GB}GB (50GB+ recommended)"
fi

echo ""

# =============================================================================
# 3. NETWORK CHECK
# =============================================================================
echo "🌐 NETWORK CONNECTIVITY"
echo "──────────────────────────────────────"

if ping -c 1 8.8.8.8 &> /dev/null; then
    check_pass "Internet connectivity: OK"
else
    check_fail "Internet connectivity: FAILED"
fi

if command -v curl &> /dev/null; then
    check_pass "curl: installed"
else
    check_warn "curl: not installed (required)"
fi

if command -v wget &> /dev/null; then
    check_pass "wget: installed"
else
    check_warn "wget: not installed (required)"
fi

if command -v git &> /dev/null; then
    check_pass "git: installed"
else
    check_warn "git: not installed"
fi

echo ""

# =============================================================================
# 4. PYTHON CHECK
# =============================================================================
echo "🐍 PYTHON ENVIRONMENT"
echo "──────────────────────────────────────"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
        check_pass "Python: $PYTHON_VERSION (3.8+)"
    else
        check_warn "Python: $PYTHON_VERSION (3.8+ recommended)"
    fi
    
    # Check pip
    if python3 -m pip --version &> /dev/null; then
        PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')
        check_pass "pip: $PIP_VERSION"
    else
        check_warn "pip: not working"
    fi
    
    # Check venv
    if python3 -m venv --help &> /dev/null; then
        check_pass "venv: available"
    else
        check_warn "venv: not available"
    fi
else
    check_fail "Python3: not found"
fi

echo ""

# =============================================================================
# 5. BUILD TOOLS CHECK
# =============================================================================
echo "🔨 BUILD TOOLS"
echo "──────────────────────────────────────"

BUILD_TOOLS=("gcc" "make" "g++")
for tool in "${BUILD_TOOLS[@]}"; do
    if command -v $tool &> /dev/null; then
        check_pass "$tool: installed"
    else
        check_warn "$tool: not installed (required)"
    fi
done

if command -v dpkg &> /dev/null; then
    if dpkg -l | grep -q build-essential; then
        check_pass "build-essential: installed"
    else
        check_warn "build-essential: not installed"
    fi
fi

echo ""

# =============================================================================
# 6. DATABASE CHECK
# =============================================================================
echo "💾 DATABASE SERVICES"
echo "──────────────────────────────────────"

if command -v redis-server &> /dev/null; then
    REDIS_VERSION=$(redis-server --version)
    check_pass "Redis: $REDIS_VERSION"
else
    check_warn "Redis: not installed (will be installed)"
fi

if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        check_pass "Redis daemon: running"
    else
        check_info "Redis: installed but not running"
    fi
fi

echo ""

# =============================================================================
# 7. SUDO ACCESS CHECK
# =============================================================================
echo "🔐 SUDO ACCESS"
echo "──────────────────────────────────────"

if sudo -n true 2>/dev/null; then
    check_pass "sudo: available without password"
else
    if sudo -l &> /dev/null; then
        check_warn "sudo: available (will require password)"
    else
        check_fail "sudo: not available"
    fi
fi

echo ""

# =============================================================================
# 8. DISK SPACE CHECK
# =============================================================================
echo "💿 DISK SPACE REQUIREMENT"
echo "──────────────────────────────────────"

REQUIRED_HOME=10
REQUIRED_ROOT=50
HOME_AVAILABLE=$(df ~/ | awk 'NR==2 {print int($4/1024/1024)}')
ROOT_AVAILABLE=$(df / | awk 'NR==2 {print int($4/1024/1024)}')

if [ $HOME_AVAILABLE -gt $((REQUIRED_HOME * 1024)) ]; then
    check_pass "Home partition: ${HOME_AVAILABLE}MB free (10GB+ for venv)"
else
    check_warn "Home partition: ${HOME_AVAILABLE}MB free (10GB+ recommended)"
fi

if [ $ROOT_AVAILABLE -gt $((REQUIRED_ROOT * 1024)) ]; then
    check_pass "Root partition: ${ROOT_AVAILABLE}MB free (50GB+ for compilation)"
else
    check_warn "Root partition: ${ROOT_AVAILABLE}MB free (50GB+ for compilation)"
fi

echo ""

# =============================================================================
# 9. PORTS CHECK
# =============================================================================
echo "🔌 PORT AVAILABILITY"
echo "──────────────────────────────────────"

PORTS=(8000 8003 8004 8005 8006 8007 8008 8011 8012 6379)
UNAVAILABLE=0

for port in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        check_warn "Port $port: in use"
        ((UNAVAILABLE++))
    else
        check_pass "Port $port: available"
    fi
done

if [ $UNAVAILABLE -eq 0 ]; then
    check_pass "All required ports available"
fi

echo ""

# =============================================================================
# 10. KERNEL PARAMETERS CHECK
# =============================================================================
echo "⚙️  KERNEL PARAMETERS"
echo "──────────────────────────────────────"

CURRENT_FD=$(cat /proc/sys/fs/file-max 2>/dev/null)
check_info "file-max: $CURRENT_FD (65536+ recommended)"

CURRENT_SOMAXCONN=$(cat /proc/sys/net/core/somaxconn 2>/dev/null)
check_info "somaxconn: $CURRENT_SOMAXCONN (1024+ recommended)"

CURRENT_BACKLOG=$(cat /proc/sys/net/ipv4/tcp_max_syn_backlog 2>/dev/null)
check_info "tcp_max_syn_backlog: $CURRENT_BACKLOG (1024+ recommended)"

echo ""

# =============================================================================
# FINAL SUMMARY
# =============================================================================
echo "════════════════════════════════════════════════════════════════"
echo "📊 CHECK SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${GREEN}✓ Passed: $PASS${NC}"
echo -e "  ${YELLOW}! Warnings: $WARN${NC}"
echo -e "  ${RED}✗ Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}✅ SYSTEM READY FOR APEX CITADEL SETUP!${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo "  1. chmod +x setup_apex_ultimate.sh"
    echo "  2. ./setup_apex_ultimate.sh"
    echo ""
    exit 0
else
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${RED}⚠️  SYSTEM HAS CRITICAL ISSUES${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Please resolve the failed checks before proceeding."
    echo ""
    exit 1
fi
