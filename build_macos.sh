#!/bin/bash

# WhisperAI Simple App Bundle Creator for macOS
# Creates a lightweight .app bundle without PyInstaller

set -e

echo "🔨 Building WhisperAI for macOS..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.spec *.icns WhisperAI.iconset

# Create app bundle structure
APP_NAME="WhisperAI"
APP_BUNDLE="dist/$APP_NAME.app"
CONTENTS="$APP_BUNDLE/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

echo "📦 Creating app bundle structure..."
mkdir -p "$MACOS"
mkdir -p "$RESOURCES"

# Convert PNG icon to ICNS
echo "🎨 Converting icon to macOS format..."
if [ -f "transcript.icon/Assets/Ikonka aplikacji Python.png" ]; then
    mkdir -p WhisperAI.iconset
    
    # Create different sizes for the iconset
    sips -z 16 16     "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_16x16.png
    sips -z 32 32     "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_16x16@2x.png
    sips -z 32 32     "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_32x32.png
    sips -z 64 64     "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_32x32@2x.png
    sips -z 128 128   "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_128x128.png
    sips -z 256 256   "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_128x128@2x.png
    sips -z 256 256   "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_256x256.png
    sips -z 512 512   "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_256x256@2x.png
    sips -z 512 512   "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_512x512.png
    sips -z 1024 1024 "transcript.icon/Assets/Ikonka aplikacji Python.png" --out WhisperAI.iconset/icon_512x512@2x.png
    
    iconutil -c icns WhisperAI.iconset
    cp WhisperAI.icns "$RESOURCES/"
    rm -rf WhisperAI.iconset
    echo "✅ Icon converted"
fi

# Create launcher script
echo "📝 Creating launcher script..."
cat > "$MACOS/$APP_NAME" << 'LAUNCHER_EOF'
#!/bin/bash

# WhisperAI App Launcher for macOS with animated loading

# Prefer the project checkout when this app is run from dist/. Fall back to
# the app bundle root when the bundle has been moved elsewhere.
LAUNCHER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$LAUNCHER_DIR" && cd ../../../.. && pwd )"
APP_ROOT="$( cd "$LAUNCHER_DIR" && cd ../.. && pwd )"

if [ -f "$PROJECT_ROOT/main.py" ] && [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    SCRIPT_DIR="$PROJECT_ROOT"
else
    SCRIPT_DIR="$APP_ROOT"
fi

LOG_FILE="$SCRIPT_DIR/.whisperai.log"

# GUI apps launched from Finder usually do not inherit shell PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Spinner animation frames
SPINNER=( '⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏' )

# Function to display spinner
show_spinner() {
    local msg="$1"
    local pid=$2
    local i=0
    
    while kill -0 $pid 2>/dev/null; do
        printf "\r${CYAN}${SPINNER[$((i % ${#SPINNER[@]}))]} ${msg}${NC}"
        ((i++))
        sleep 0.1
    done

    wait "$pid"
    local status=$?

    if [ "$status" -eq 0 ]; then
        printf "\r${GREEN}✓${NC} ${msg}\n"
    else
        printf "\r${RED}✗${NC} ${msg}\n"
    fi
    return "$status"
}

# Function for initial welcome screen
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

# Log function
log_msg() {
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

# Main launcher logic
{
    echo "=== WhisperAI Launcher Started ==="
    echo "Time: $(date)"
    echo "Script Dir: $SCRIPT_DIR"
    
    show_welcome
    
    # Check Python
    echo -n "${CYAN}○${NC} Checking Python... "
    if ! command -v python3 &> /dev/null; then
        echo "${RED}✗ Python 3 not found${NC}"
        log_msg "ERROR: Python 3 not found"
        exit 1
    fi
    echo "${GREEN}✓${NC}"
    log_msg "Python: $(python3 --version)"
    
    # Check requirements.txt
    echo -n "${CYAN}○${NC} Checking files... "
    if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "${RED}✗ requirements.txt not found${NC}"
        log_msg "ERROR: requirements.txt not found"
        exit 1
    fi
    echo "${GREEN}✓${NC}"
    
    VENV_PATH="$SCRIPT_DIR/venv"
    
    # Check/create venv
    echo -n "${CYAN}○${NC} Preparing virtual environment... "
    if [ ! -d "$VENV_PATH" ]; then
        (PYTHONPATH= python3 -m venv "$VENV_PATH" >> "$LOG_FILE" 2>&1) &
        show_spinner "Preparing virtual environment" $!
    else
        echo "${GREEN}✓${NC}"
    fi
    
    # Activate venv
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo "${RED}✗ Failed to create venv${NC}"
        log_msg "ERROR: Failed to create venv"
        exit 1
    fi
    
    source "$VENV_PATH/bin/activate"
    log_msg "Virtual environment activated: $VIRTUAL_ENV"

    PYTHON_CMD=("$VENV_PATH/bin/python")
    TORCH_DEPS="$VENV_PATH/lib/python3.9/site-packages/torch/lib/libtorch_global_deps.dylib"

    if [ "$(uname -m)" = "arm64" ] && [ -f "$TORCH_DEPS" ] && file "$TORCH_DEPS" | grep -q "x86_64"; then
        if arch -x86_64 /usr/bin/true 2>/dev/null; then
            PYTHON_CMD=(arch -x86_64 "$VENV_PATH/bin/python")
            echo "${YELLOW}○${NC} Using x86_64 Python for the existing Torch install"
            log_msg "Using x86_64 Python for the existing Torch install"
        else
            echo "${RED}✗ Torch is installed for x86_64, but Rosetta is not available.${NC}"
            log_msg "ERROR: x86_64 Torch found, but Rosetta is unavailable"
            exit 1
        fi
    fi
    
    # Upgrade pip
    echo -n "${CYAN}○${NC} Updating pip... "
    ("${PYTHON_CMD[@]}" -m pip install -q --upgrade pip >> "$LOG_FILE" 2>&1) &
    if ! show_spinner "Updating pip" $!; then
        echo "${RED}✗ Failed to update pip${NC}"
        log_msg "ERROR: Failed to update pip"
        exit 1
    fi
    
    # Install requirements
    echo -n "${CYAN}○${NC} Installing dependencies... "
    echo "   (This may take 3-5 minutes on first run)"
    echo ""
    
    # Show visual progress
    ("${PYTHON_CMD[@]}" -m pip install -r "$SCRIPT_DIR/requirements.txt" >> "$LOG_FILE" 2>&1) &
    PIP_PID=$!

    if ! show_spinner "Installing dependencies" $PIP_PID; then
        echo "${RED}✗ Installation failed${NC}"
        log_msg "ERROR: Failed to install requirements"
        exit 1
    fi
    
    # Check ffmpeg
    echo -n "${CYAN}○${NC} Checking ffmpeg... "
    if ! command -v ffmpeg &> /dev/null; then
        echo "${RED}✗ Not installed${NC}"
        echo ""
        echo "${YELLOW}Please install ffmpeg using:${NC}"
        echo "  ${CYAN}brew install ffmpeg${NC}"
        log_msg "ERROR: ffmpeg not installed"
        exit 1
    fi
    echo "${GREEN}✓${NC}"
    
    # Final setup
    echo ""
    echo "${GREEN}All checks passed!${NC}"
    echo ""
    echo "${CYAN}🚀 Starting WhisperAI...${NC}"
    echo ""
    
    log_msg "Starting GUI application"
    
    # Run the application
    cd "$SCRIPT_DIR"
    "${PYTHON_CMD[@]}" main.py
    
} 2>&1 | tee -a "$LOG_FILE"

LAUNCHER_EOF

chmod +x "$MACOS/$APP_NAME"

# Create Info.plist
echo "📋 Creating Info.plist..."
cat > "$CONTENTS/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>WhisperAI</string>
    <key>CFBundleIdentifier</key>
    <string>com.whisperai.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>WhisperAI</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 WhisperAI. All rights reserved.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>CFBundleIconFile</key>
    <string>WhisperAI</string>
</dict>
</plist>
EOF

# Copy Python files to app bundle for reference
cp main.py "$APP_BUNDLE/"
cp formatter.py "$APP_BUNDLE/"
cp requirements.txt "$APP_BUNDLE/"

# Make it executable
chmod +x "$MACOS/$APP_NAME"

echo ""
echo "✅ Build successful!"
echo ""
echo "📂 Output: $APP_BUNDLE"
echo ""
echo "To run the app:"
echo "  open dist/$APP_NAME.app"
echo ""
echo "To install to Applications folder:"
echo "  cp -r dist/$APP_NAME.app /Applications/"
echo ""
echo "Or run directly from terminal:"
echo "  bash run.sh"
