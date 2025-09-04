#!/bin/bash
# Quick user verification and hostname fix script

echo "Current User Information"
echo "======================="
echo "Username: $(whoami)"
echo "Home directory: $(eval echo ~$(whoami))"
echo "Groups: $(groups)"
echo "Hostname: $(hostname)"
echo ""

# Fix hostname resolution
echo "Fixing hostname resolution..."
HOSTNAME=$(hostname)
if ! grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts 2>/dev/null; then
    echo "Adding hostname to /etc/hosts..."
    echo "127.0.1.1    $HOSTNAME" | sudo tee -a /etc/hosts > /dev/null
    echo "✓ Hostname resolution fixed"
else
    echo "✓ Hostname already configured"
fi

echo ""
echo "Test sudo access..."
if sudo -v 2>/dev/null; then
    echo "✓ Sudo access confirmed"
else
    echo "✗ Sudo access failed - you may need to be added to sudo group"
    echo "Run: sudo usermod -a -G sudo $(whoami)"
fi

echo ""
echo "Testing Python and tkinter..."
python3 --version
python3 -c "import tkinter; print('✓ tkinter is available')" || echo "✗ tkinter not available - need to install python3-tk"

echo ""
echo "Ready for installation!"
echo "Use one of these scripts:"
echo "  ./install_fixed.sh    (recommended - handles all issues)"
echo "  ./install_manual.sh   (step-by-step with user prompts)"
