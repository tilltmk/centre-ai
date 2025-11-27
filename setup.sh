#!/bin/bash
#
# Centre AI - MCP Server Setup Script
# Interactive setup wizard for configuring your secure MCP server
#
# Usage: ./setup.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
DATA_DIR="./data"
GIT_REPOS_DIR="./git_repos"

# ========================================
# HELPER FUNCTIONS
# ========================================

print_banner() {
    clear
    echo -e "${WHITE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                       C E N T R E                            ║"
    echo "║                                                              ║"
    echo "║              AI Knowledge Server · MCP Protocol              ║"
    echo "║                                                              ║"
    echo "║                        Version 2.0.0                         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

print_error() {
    echo -e "${RED}✗ ${NC}$1"
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local is_password="$4"

    if [ -n "$default" ]; then
        prompt="${prompt} [${default}]"
    fi

    echo -ne "${WHITE}${prompt}: ${NC}"

    if [ "$is_password" = "true" ]; then
        read -s input
        echo ""
    else
        read input
    fi

    if [ -z "$input" ] && [ -n "$default" ]; then
        eval "$var_name='$default'"
    else
        eval "$var_name='$input'"
    fi
}

generate_secret() {
    openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | base64 | tr -d '\n' | head -c 64
}

validate_port() {
    local port=$1
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        return 1
    fi
    return 0
}

check_dependencies() {
    print_step "Checking Dependencies"

    local missing=()

    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    else
        print_success "Docker installed: $(docker --version | cut -d' ' -f3 | tr -d ',')"
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing+=("docker-compose")
    else
        if docker compose version &> /dev/null; then
            print_success "Docker Compose installed: $(docker compose version --short)"
        else
            print_success "Docker Compose installed: $(docker-compose --version | cut -d' ' -f3 | tr -d ',')"
        fi
    fi

    if ! command -v openssl &> /dev/null; then
        print_warning "OpenSSL not found - using fallback for secret generation"
    else
        print_success "OpenSSL installed"
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        echo ""
        print_error "Missing required dependencies: ${missing[*]}"
        echo ""
        echo "Please install the missing dependencies and run this script again."
        exit 1
    fi

    echo ""
    print_success "All dependencies satisfied"
    echo ""
}

# ========================================
# CONFIGURATION STEPS
# ========================================

configure_admin() {
    print_step "Administrator Configuration"

    print_info "Configure the admin account for the web interface."
    echo ""

    prompt_input "Admin Username" "admin" ADMIN_USERNAME
    prompt_input "Admin Password" "" ADMIN_PASSWORD "true"

    while [ -z "$ADMIN_PASSWORD" ] || [ ${#ADMIN_PASSWORD} -lt 8 ]; do
        print_warning "Password must be at least 8 characters"
        prompt_input "Admin Password" "" ADMIN_PASSWORD "true"
    done

    echo ""
    print_success "Admin credentials configured"
    echo ""
}

configure_security() {
    print_step "Security Configuration"

    print_info "Generating secure tokens for authentication..."
    echo ""

    SECRET_KEY=$(generate_secret)
    MCP_AUTH_TOKEN=$(generate_secret)

    print_success "Secret key generated"
    print_success "MCP authentication token generated"

    echo ""
    echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${YELLOW}│ ${WHITE}IMPORTANT: Save your MCP authentication token!${YELLOW}                  │${NC}"
    echo -e "${YELLOW}│                                                                 │${NC}"
    echo -e "${YELLOW}│ ${NC}Token: ${CYAN}${MCP_AUTH_TOKEN:0:32}...${YELLOW}       │${NC}"
    echo -e "${YELLOW}│                                                                 │${NC}"
    echo -e "${YELLOW}│ ${NC}You'll need this token to connect AI clients to your server.${YELLOW}  │${NC}"
    echo -e "${YELLOW}│ ${NC}It will also be saved in your .env file.${YELLOW}                      │${NC}"
    echo -e "${YELLOW}└─────────────────────────────────────────────────────────────────┘${NC}"
    echo ""

    read -p "Press Enter to continue..."
    echo ""
}

configure_database() {
    print_step "Database Configuration"

    print_info "Configure PostgreSQL database credentials."
    echo ""

    prompt_input "Database Name" "centre_ai" POSTGRES_DB
    prompt_input "Database User" "centre_ai" POSTGRES_USER
    prompt_input "Database Password" "" POSTGRES_PASSWORD "true"

    while [ -z "$POSTGRES_PASSWORD" ] || [ ${#POSTGRES_PASSWORD} -lt 8 ]; do
        print_warning "Password must be at least 8 characters"
        prompt_input "Database Password" "" POSTGRES_PASSWORD "true"
    done

    echo ""
    print_success "Database configured"
    echo ""
}

configure_ports() {
    print_step "Port Configuration"

    print_info "Configure network ports for the services."
    print_info "Default ports: MCP Server (2068), Admin UI (2069)"
    echo ""

    prompt_input "MCP Server Port" "2068" MCP_PORT

    while ! validate_port "$MCP_PORT"; do
        print_warning "Invalid port number"
        prompt_input "MCP Server Port" "2068" MCP_PORT
    done

    prompt_input "Admin UI Port" "2069" ADMIN_PORT

    while ! validate_port "$ADMIN_PORT"; do
        print_warning "Invalid port number"
        prompt_input "Admin UI Port" "2069" ADMIN_PORT
    done

    if [ "$MCP_PORT" = "$ADMIN_PORT" ]; then
        print_warning "Ports cannot be the same. Using defaults."
        MCP_PORT=2068
        ADMIN_PORT=2069
    fi

    echo ""
    print_success "Ports configured: MCP=$MCP_PORT, Admin=$ADMIN_PORT"
    echo ""
}

configure_logging() {
    print_step "Logging Configuration"

    print_info "Configure logging level."
    echo ""

    echo "Available levels:"
    echo "  1) DEBUG   - Verbose debugging information"
    echo "  2) INFO    - General operational information"
    echo "  3) WARNING - Warning messages only"
    echo "  4) ERROR   - Error messages only"
    echo ""

    prompt_input "Select logging level (1-4)" "2" LOG_CHOICE

    case $LOG_CHOICE in
        1) LOG_LEVEL="DEBUG" ;;
        2) LOG_LEVEL="INFO" ;;
        3) LOG_LEVEL="WARNING" ;;
        4) LOG_LEVEL="ERROR" ;;
        *) LOG_LEVEL="INFO" ;;
    esac

    echo ""
    print_success "Logging level set to: $LOG_LEVEL"
    echo ""
}

# ========================================
# WRITE CONFIGURATION
# ========================================

write_env_file() {
    print_step "Writing Configuration"

    cat > "$ENV_FILE" << EOF
# Centre AI - MCP Server Configuration
# Generated: $(date)

# ========================================
# ADMIN CREDENTIALS
# ========================================
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# ========================================
# SECURITY TOKENS
# ========================================
SECRET_KEY=${SECRET_KEY}
MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}

# ========================================
# DATABASE
# ========================================
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# ========================================
# PORTS (exposed to localhost only)
# ========================================
MCP_PORT=${MCP_PORT}
ADMIN_PORT=${ADMIN_PORT}

# ========================================
# LOGGING
# ========================================
LOG_LEVEL=${LOG_LEVEL}

# ========================================
# INTERNAL SERVICES (do not modify)
# ========================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
QDRANT_HOST=qdrant
QDRANT_PORT=6333
REDIS_HOST=redis
REDIS_PORT=6379
EOF

    chmod 600 "$ENV_FILE"
    print_success "Configuration written to $ENV_FILE"
    echo ""
}

create_directories() {
    print_info "Creating data directories..."

    mkdir -p "$DATA_DIR"
    mkdir -p "$GIT_REPOS_DIR"

    print_success "Data directories created"
    echo ""
}

# ========================================
# DOCKER OPERATIONS
# ========================================

build_containers() {
    print_step "Building Docker Containers"

    print_info "This may take several minutes on first run..."
    echo ""

    if docker compose version &> /dev/null; then
        docker compose build --no-cache
    else
        docker-compose build --no-cache
    fi

    echo ""
    print_success "Containers built successfully"
    echo ""
}

start_services() {
    print_step "Starting Services"

    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    echo ""
    print_info "Waiting for services to become healthy..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker compose ps 2>/dev/null | grep -q "healthy" || docker-compose ps 2>/dev/null | grep -q "healthy"; then
            break
        fi
        sleep 2
        attempt=$((attempt + 1))
        echo -ne "\r  Checking health... ($attempt/$max_attempts)"
    done
    echo ""

    if [ $attempt -eq $max_attempts ]; then
        print_warning "Services may still be starting. Check logs with: docker compose logs"
    else
        print_success "All services started successfully"
    fi
    echo ""
}

# ========================================
# SUMMARY
# ========================================

print_summary() {
    print_step "Setup Complete!"

    echo -e "${WHITE}Your Centre AI MCP Server is now running.${NC}"
    echo ""
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│                         ACCESS URLS                             │${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}Admin Web UI:${NC}    http://localhost:${ADMIN_PORT}                       ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}MCP SSE Endpoint:${NC} http://localhost:${MCP_PORT}/sse                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│                       CREDENTIALS                               │${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}Admin Username:${NC}  ${ADMIN_USERNAME}                                          ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}Admin Password:${NC}  ********                                       ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│                     MCP CLIENT CONFIG                           │${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  Add this to your MCP client configuration:                    ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}{${NC}                                                            ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}    ${WHITE}\"mcpServers\": {${NC}                                             ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}      ${WHITE}\"centre-ai\": {${NC}                                            ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}        ${WHITE}\"url\": \"http://localhost:${MCP_PORT}/sse\",${NC}                   ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}        ${WHITE}\"transport\": \"sse\",${NC}                                     ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}        ${WHITE}\"headers\": {${NC}                                             ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}          ${WHITE}\"Authorization\": \"Bearer <YOUR_TOKEN>\"${NC}                 ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}        ${WHITE}}${NC}                                                        ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}      ${WHITE}}${NC}                                                          ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}    ${WHITE}}${NC}                                                            ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}}${NC}                                                              ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  Find your token in .env file or Admin UI Settings            ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                                 ${CYAN}│${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -e "${WHITE}Useful Commands:${NC}"
    echo ""
    echo "  View logs:         docker compose logs -f"
    echo "  Stop services:     docker compose down"
    echo "  Restart services:  docker compose restart"
    echo "  Check status:      docker compose ps"
    echo ""
    echo -e "${GREEN}Thank you for using Centre AI!${NC}"
    echo ""
}

# ========================================
# MAIN
# ========================================

main() {
    print_banner

    echo -e "${WHITE}Welcome to the Centre AI setup wizard.${NC}"
    echo ""
    echo "This script will help you configure and start your secure MCP server."
    echo "You can re-run this script at any time to reconfigure."
    echo ""
    read -p "Press Enter to begin setup..."
    echo ""

    check_dependencies
    configure_admin
    configure_security
    configure_database
    configure_ports
    configure_logging
    write_env_file
    create_directories

    echo ""
    echo -e "${WHITE}Configuration complete. Ready to build and start services.${NC}"
    echo ""
    read -p "Build and start containers now? [Y/n]: " START_NOW

    if [[ "$START_NOW" =~ ^[Nn]$ ]]; then
        echo ""
        print_info "You can start the services later with: docker compose up -d"
        echo ""
        exit 0
    fi

    build_containers
    start_services
    print_summary
}

# Run main function
main "$@"
