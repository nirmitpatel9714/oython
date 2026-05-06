#!/bin/bash

echo "🚀 Installing Oython..."

# Create installation directory
INSTALL_DIR="$HOME/.oython"
mkdir -p "$INSTALL_DIR"

# Copy the core interpreter
if [ ! -f "oython.py" ]; then
    echo "❌ Error: oython.py not found in the current directory."
    echo "Please run this script from the Oython repository root."
    exit 1
fi

cp oython.py "$INSTALL_DIR/"

# Create wrapper script in ~/.local/bin
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

WRAPPER="$BIN_DIR/oython"

echo '#!/bin/bash' > "$WRAPPER"
echo "python3 \"$INSTALL_DIR/oython.py\" \"\$@\"" >> "$WRAPPER"

chmod +x "$WRAPPER"

echo "✅ Oython installed successfully!"
echo "============================================================"
echo "⚠️  IMPORTANT: Make sure $BIN_DIR is in your PATH."
echo "If it is not, add the following line to your ~/.bashrc or ~/.zshrc:"
echo "export PATH=\"\$PATH:$BIN_DIR\""
echo "============================================================"
