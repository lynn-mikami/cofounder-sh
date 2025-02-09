#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

MODEL_TYPE="openai"

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
    local model="${2:-openai}"  # Default to openai if not specified
    
    echo -e "\n${YELLOW}=== Mission Received ====${NC}"
    echo -e "${BLUE}Task: ${CYAN}$task${NC}\n"
    
    show_loading_animation "Powering up AI systems"
    
    case $model in
        "deepseek")
            echo -e "${CYAN}DeepSeek systems online!${NC}"
            script="main-deepseek.py"
            ;;
        "claude")
            echo -e "${CYAN}Claude systems online!${NC}"
            script="main-claude.py"
            ;;
        *)
            echo -e "${CYAN}OpenAI systems online!${NC}"
            script="main.py"
            ;;
    esac
    
    echo -e "\n${YELLOW}=== Mission Start! ====${NC}"
    show_loading_animation "Initializing AI systems"
    
    python src/$script "$task"
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

run_examples() {
    echo -e "\n${YELLOW}=== Voyager Mode ====${NC}"
    
    if [ ! -d "examples" ]; then
        echo -e "${RED}Error: examples directory not found${NC}"
        exit 1
    fi
    
    examples=()
    while IFS= read -r -d $'\0' file; do
        examples+=("$file")
    done < <(find examples -name "*.py" -print0)
    
    if [ ${#examples[@]} -eq 0 ]; then
        echo -e "${RED}No example files found in examples directory${NC}"
        exit 1
    fi
    
    echo -e "\n${BLUE}Select an example to run:${NC}\n"
    
    # Display all examples with numbers and clean names
    for i in "${!examples[@]}"; do
        # Convert filename to readable format:
        # 1. Remove 'examples/' prefix and '.py' extension
        # 2. Replace underscores with spaces
        # 3. Capitalize only the first letter of the entire name
        # 4. Replace 'b' with 'u' in the filename
        clean_name=$(basename "${examples[$i]}" .py | sed 's/_/ /g' | sed -E 's/\<([a-z])/\U\1/g')
        echo "$((i+1)). ${clean_name}"
    done
    
    # Get user choice
    read -p "Enter your choice (1-${#examples[@]}): " choice
    
    if [ "$choice" -ge 1 ] && [ "$choice" -le "${#examples[@]}" ]; then
        selected_example="${examples[$((choice-1))]}"
        echo -e "\n${CYAN}Running example: ${BLUE}${selected_example}${NC}"
        show_loading_animation "Preparing example"
        python "$selected_example"
        echo -e "${GREEN}✅ Example completed: ${selected_example}${NC}"
    else
        echo -e "${RED}Invalid selection${NC}"
        exit 1
    fi
}

read_actions() {
    # Model selection with retro game style
    echo -e "\n${YELLOW}=== LEVEL 1: Choose Your AI Companion ====${NC}"
    echo -e "\n${BLUE}Select your AI partner:${NC}"
    echo "1. 🤖 OpenAI (Production Ready)"
    echo "2. 🚀 DeepSeek (Experimental)"
    echo "3. 🌌 Claude (Experimental)"
    echo "4. 🦙 Ollama (Experimental) [Coming Soon]"
    read -p "Enter your choice (1-4): " model_choice
    
    show_loading_animation "Powering up AI systems"
    
    # Set script based on model choice
    case $model_choice in
        1)
            echo -e "${CYAN}OpenAI systems online!${NC}"
            script="main.py"
            ;;
        2)
            echo -e "${CYAN}DeepSeek systems online!${NC}"
            script="main-deepseek.py"
            ;;
        3)
            echo -e "${CYAN}Claude systems online!${NC}"
            script="main-claude.py"
            ;;
        4)
            echo -e "${RED}Ollama support coming soon!${NC}"
            exit 1
            ;;
        *)
            echo -e "${RED}Invalid selection. Defaulting to OpenAI.${NC}"
            script="main.py"
            ;;
    esac

    echo -e "\n${YELLOW}=== LEVEL 2: Select Your Mission ====${NC}"
    
    if [ ! -f "prompts.md" ]; then
        echo -e "${RED}Critical Error: Mission database (prompts.md) not found${NC}"
        exit 1
    fi

    echo -e "${BLUE}Available Missions:${NC}\n"
    
    tasks=()
    while IFS= read -r line; do
        if [[ "$line" =~ ^#|^$ ]]; then
            continue
        fi
        tasks+=("$line")
    done < <(sed 's/^[[:space:]]*//' prompts.md)

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
elif [ "$1" = "--voyager" ]; then
    ensure_venv
    run_examples
elif [ "$1" = "--model" ] || [ "$1" = "-m" ]; then
    if [ -z "$2" ]; then
        echo -e "${RED}Error: Model type required${NC}"
        exit 1
    fi
    MODEL_TYPE="$2"
    if [ -n "$3" ]; then
        # Execute with specified model and task
        execute_task "${@:3}" "$MODEL_TYPE"
    else
        # Run interactive mode with specified model
        run_main "$MODEL_TYPE"
    fi
elif [ -n "$1" ]; then
    # If there's a command line argument, use it as the task
    ensure_venv
    execute_task "$*" "$MODEL_TYPE"
else
    # No arguments - run interactive mode
    run_main "$MODEL_TYPE"
fi