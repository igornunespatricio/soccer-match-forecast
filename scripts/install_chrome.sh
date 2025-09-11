#!/bin/bash

# Chrome and ChromeDriver Installer for Ubuntu (Non-interactive)
# Designed for CI/CD pipelines - no user input required
# Usage: ./install_chrome_pipeline.sh

set -e  # Exit on any error

# Exit codes
SUCCESS=0
FAILURE=1

# Log functions
log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# Check if running as root, use sudo if not
ensure_sudo() {
    if [ "$EUID" -ne 0 ]; then
        if ! command -v sudo >/dev/null 2>&1; then
            log_error "sudo not available and not running as root"
            exit $FAILURE
        fi
    fi
}

# Install Google Chrome
install_chrome() {
    if command -v google-chrome >/dev/null 2>&1; then
        log_info "Google Chrome already installed: $(google-chrome --version)"
        return 0
    fi

    log_info "Installing Google Chrome..."
    
    # Download Chrome .deb package
    if ! wget -q --timeout=30 --tries=3 https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; then
        log_error "Failed to download Chrome package"
        return $FAILURE
    fi

    # Install Chrome
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq
        apt-get install -y -qq ./google-chrome-stable_current_amd64.deb
    else
        dpkg -i google-chrome-stable_current_amd64.deb
        apt-get install -y -qq -f  # Fix dependencies
    fi

    # Clean up
    rm -f google-chrome-stable_current_amd64.deb
    
    if ! command -v google-chrome >/dev/null 2>&1; then
        log_error "Chrome installation failed"
        return $FAILURE
    fi
    
    log_success "Chrome installed: $(google-chrome --version)"
    return 0
}

# Install ChromeDriver
install_chromedriver() {
    if command -v chromedriver >/dev/null 2>&1; then
        log_info "ChromeDriver already installed: $(chromedriver --version)"
        return 0
    fi

    log_info "Installing ChromeDriver..."
    
    # Try multiple installation methods
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq
        
        # Method 1: Install from repository
        if apt-get install -y -qq chromium-chromedriver 2>/dev/null; then
            if command -v chromedriver >/dev/null 2>&1; then
                log_success "ChromeDriver installed via apt: $(chromedriver --version)"
                return 0
            fi
        fi

        # Method 2: Manual installation
        log_info "Trying manual ChromeDriver installation..."
        local CHROME_VERSION=$(google-chrome --version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
        local CHROMEDRIVER_VERSION="${CHROME_VERSION%.*}"
        local CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
        
        if wget -q --timeout=30 "$CHROMEDRIVER_URL"; then
            unzip -q chromedriver_linux64.zip
            chmod +x chromedriver
            mv chromedriver /usr/local/bin/
            rm chromedriver_linux64.zip
            
            if command -v chromedriver >/dev/null 2>&1; then
                log_success "ChromeDriver installed manually: $(chromedriver --version)"
                return 0
            fi
        fi
    fi

    log_error "ChromeDriver installation failed"
    return $FAILURE
}

# Verify installations work
verify_installations() {
    log_info "Verifying installations..."
    
    if ! command -v google-chrome >/dev/null 2>&1; then
        log_error "Chrome not found after installation"
        return $FAILURE
    fi

    if ! command -v chromedriver >/dev/null 2>&1; then
        log_error "ChromeDriver not found after installation"
        return $FAILURE
    fi

    # Test headless Chrome
    if timeout 30s google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.example.com >/dev/null 2>&1; then
        log_success "Headless Chrome test passed"
    else
        log_error "Headless Chrome test failed"
        return $FAILURE
    fi

    return 0
}

# Main execution
main() {
    log_info "Starting Chrome and ChromeDriver installation..."
    
    ensure_sudo
    
    if ! install_chrome; then
        exit $FAILURE
    fi
    
    if ! install_chromedriver; then
        exit $FAILURE
    fi
    
    if ! verify_installations; then
        exit $FAILURE
    fi
    
    log_success "Installation completed successfully"
    exit $SUCCESS
}

# Run main function
main "$@"