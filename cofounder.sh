#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ensure_venv() {
    if [ -d "venv" ]; then
        # Try to activate the virtual environment
        if ! source venv/bin/activate 2>/dev/null; then
            echo -e "${RED}Failed to activate virtual environment${NC}"
            echo -e "${YELLOW}Try running: ${CYAN}source venv/bin/activate${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Virtual environment activated${NC}"  # Add this line here
    else
        echo -e "${YELLOW}Virtual environment not found. Setting up now...${NC}"
        setup_environment
    fi
}

show_welcome() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
       ______      ______                    __                    __
      / ____/___  / __/ /_  __  ______  ____/ /__  _____ _____  / /_
     / /   / __ \/ /_/ __ \/ / / / __ \/ __  / _ \/ ___// ___/ / __ \
    / /___/ /_/ / __/ /_/ / /_/ / / / / /_/ /  __/ /   (__  ) / / / /
    \____/\____/_/ /_.___/\__,_/_/ /_/\__,_/\___/_/ (_)____/ / / /_/
                                                    
EOF
    echo -e "${NC}"
}

execute_task() {
    local task="$1"
    echo -e "\n${YELLOW}=== Mission Received ====${NC}"
    echo -e "${BLUE}Task: ${CYAN}$task${NC}\n"
    
    show_loading_animation "Powering up AI systems"
    echo -e "${CYAN}OpenAI systems online!${NC}"
    
    echo -e "\n${YELLOW}=== Mission Start! ====${NC}"
    show_loading_animation "Initializing AI systems"
    
    python src/main.py "$task"
}

show_loading_animation() {
    local message="$1"
    local chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    for (( i=0; i<15; i++ )); do
        for (( j=0; j<${#chars}; j++ )); do
            echo -en "\r${CYAN}${message} ${chars:$j:1} ${NC}"
            sleep 0.1
        done
    done
    echo
}

read_actions() {
    # Model selection with retro game style
    echo -e "\n${YELLOW}=== LEVEL 1: Choose Your AI Companion ====${NC}"
    echo -e "\n${BLUE}Select your AI partner:${NC}"
    echo "1. 🤖 OpenAI (Production Ready)"
    echo "2. 🚀 DeepSeek (Experimental) [Coming Soon]"
    echo "3. 🌌 Gemini (Experimental) [Coming Soon]"
    echo "4. 🦙 Ollama (Experimental) [Coming Soon]"
    read -p "Enter your choice (1-4): " model_choice
    
    show_loading_animation "Powering up AI systems"
    
    # Force OpenAI selection until others are ready
    echo -e "${CYAN}OpenAI systems online!${NC}"
    script="main.py"

    echo -e "\n${YELLOW}=== LEVEL 2: Select Your Mission ====${NC}"
    
    if [ ! -f "actions.md" ]; then
        echo -e "${RED}Critical Error: Mission database (actions.md) not found${NC}"
        exit 1
    fi

    echo -e "${BLUE}Available Missions:${NC}\n"
    
    tasks=()
    while IFS= read -r line; do
        if [[ "$line" =~ ^#|^$ ]]; then
            continue
        fi
        tasks+=("$line")
    done < <(sed 's/^[[:space:]]*//' actions.md)

    if [ ${#tasks[@]} -eq 0 ]; then
        echo -e "${RED}Error: No missions available${NC}"
        exit 1
    fi
    
    for i in "${!tasks[@]}"; do
        echo "[$((i+1))] ${tasks[$i]}"
    done
    echo "[${#tasks[@]}+1] 🎯 Custom mission"
    
    read -p "Select your mission (1-$((${#tasks[@]}+1))): " choice
    
    show_loading_animation "Preparing mission parameters"
    
    if [ "$choice" -le "${#tasks[@]}" ] 2>/dev/null; then
        task="${tasks[$((choice-1))]}"
    elif [ "$choice" -eq "$((${#tasks[@]}+1))" ]; then
        echo -e "${CYAN}Enter your custom mission briefing:${NC}"
        read -p "> " task
    else
        echo -e "${RED}Mission aborted: Invalid selection${NC}"
        exit 1
    fi
    
    echo -e "\n${YELLOW}=== LEVEL 3: Mission Start! ====${NC}"
    show_loading_animation "Initializing AI systems"
    
    python src/$script "$task"
}

setup_environment() {
    echo -e "${BLUE}🔧 Setting up development environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv || { 
            echo -e "${RED}Failed to create virtual environment${NC}"
            exit 1
        }
    fi
    
    # Activate virtual environment
    source venv/bin/activate || {
        echo -e "${RED}Failed to activate virtual environment${NC}"
        exit 1
    }
    
    # Install requirements
    pip install -r requirements.txt || {
        echo -e "${RED}Failed to install requirements${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✅ Environment setup complete!${NC}"
}

run_main() {
    ensure_venv
    read_actions
}

# Show welcome screen
show_welcome

# Main execution logic
if [ "$1" = "setup" ]; then
    setup_environment
elif [ -n "$1" ]; then
    # If there's a command line argument, use it as the task
    ensure_venv
    execute_task "$*"
else
    # No arguments - run interactive mode
    run_main
fi