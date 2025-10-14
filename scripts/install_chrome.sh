#!/bin/bash

# Install Chrome system-wide with sudo
set -e

echo "Installing Chrome for Selenium..."

# Update package list and install Chrome
sudo apt update
sudo apt install -y wget

# Download and install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

sudo apt update
sudo apt install -y google-chrome-stable

echo "Chrome installed successfully!"
echo "Chrome version: $(google-chrome --version)"