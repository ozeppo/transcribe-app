#!/bin/bash
# WhisperAI Launcher with animated loading

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# GUI apps and non-login shells often miss Homebrew paths.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Spinner frames
SPINNER=( '⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏' )

show_spinner() {
    local msg="$1"
    local pid=$2
    local i=0
    
    while kill -0 $pid 2>/dev/null; do
        printf "\r${CYAN}${SPINNER[$((i % ${#SPINNER[@]}))]} ${msg}${NC}"
        ((i++))
        sleep 0.1
    done

    set +e
    wait "$pid"
    local status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        printf "\r${GREEN}✓${NC} ${msg}\n"
    else
        printf "\r${RED}✗${NC} ${msg}\n"
    fi
    return "$status"
}

show_welcome() {
    [ -t 1 ] && clear
    echo ""
    echo "  ${BLUE}╔══════════════════════════════════════╗${NC}"
    echo "  ${BLUE}║${NC}                                      ${BLUE}║${NC}"
    echo "  ${BLUE}║${NC}      ${CYAN}🎤 WhisperAI v1.0.0${NC}         ${BLUE}║${NC}"
    echo "  ${BLUE}║${NC}   Speech-to-Subtitle Generator   ${BLUE}║${NC}"
    echo "  ${BLUE}║${NC}                                      ${BLUE}║${NC}"
    echo "  ${BLUE}╚══════════════════════════════════════╝${NC}"
    echo ""
}

show_welcome

# Check Python
echo -n "${CYAN}○${NC} Checking Python... "
if ! command -v python3 &> /dev/null; then
    echo "${RED}✗${NC}"
    echo "Python 3 is not installed!"
    echo "Please install Python 3.9 or higher from python.org"
    exit 1
fi
echo "${GREEN}✓${NC}"

# Check requirements
echo -n "${CYAN}○${NC} Checking files... "
if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "${RED}✗${NC}"
    echo "requirements.txt not found!"
    exit 1
fi
echo "${GREEN}✓${NC}"

VENV_PATH="$SCRIPT_DIR/venv"

# Create or check venv
echo -n "${CYAN}○${NC} Preparing environment... "
if [ ! -d "$VENV_PATH" ]; then
    (PYTHONPATH= python3 -m venv "$VENV_PATH" 2>/dev/null) &
    show_spinner "Preparing environment" $!
else
    echo "${GREEN}✓${NC}"
fi

# Activate venv
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "${RED}✗ Failed to create virtual environment${NC}"
    exit 1
fi

source "$VENV_PATH/bin/activate"

PYTHON_CMD=("$VENV_PATH/bin/python")
TORCH_DEPS="$VENV_PATH/lib/python3.9/site-packages/torch/lib/libtorch_global_deps.dylib"

if [ "$(uname -m)" = "arm64" ] && [ -f "$TORCH_DEPS" ] && file "$TORCH_DEPS" | grep -q "x86_64"; then
    if arch -x86_64 /usr/bin/true 2>/dev/null; then
        PYTHON_CMD=(arch -x86_64 "$VENV_PATH/bin/python")
        echo "${YELLOW}○${NC} Using x86_64 Python for the existing Torch install"
    else
        echo "${RED}✗${NC} Torch is installed for x86_64, but Rosetta is not available."
        echo "Recreate the virtual environment with an arm64 Python or install Rosetta."
        exit 1
    fi
fi

# Update pip
echo -n "${CYAN}○${NC} Updating pip... "
("${PYTHON_CMD[@]}" -m pip install -q --upgrade pip 2>/dev/null) &
if ! show_spinner "Updating pip" $!; then
    echo "${RED}Failed to update pip${NC}"
    exit 1
fi

# Install dependencies
echo -n "${CYAN}○${NC} Installing dependencies... "
("${PYTHON_CMD[@]}" -m pip install -q -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null) &
if ! show_spinner "Installing dependencies" $!; then
    echo "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Check ffmpeg
echo -n "${CYAN}○${NC} Checking ffmpeg... "
if ! command -v ffmpeg &> /dev/null; then
    echo "${RED}✗${NC}"
    echo ""
    echo "${YELLOW}ffmpeg is not installed!${NC}"
    echo "Please install it using: ${CYAN}brew install ffmpeg${NC}"
    exit 1
fi
echo "${GREEN}✓${NC}"

# Launch
echo ""
echo "${GREEN}All systems ready!${NC}"
echo ""
echo "${CYAN}🚀 Starting WhisperAI...${NC}"
echo ""

cd "$SCRIPT_DIR"
"${PYTHON_CMD[@]}" main.py
