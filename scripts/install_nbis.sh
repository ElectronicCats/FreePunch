#!/bin/bash
# Install NBIS from official NIST source

set -e

echo "Installing NBIS (NIST Biometric Image Software)..."

# Install dependencies
sudo apt-get update
sudo apt-get install -y build-essential libpng-dev libjpeg-dev wget

# Download from NIST
cd /tmp
wget https://nigos.nist.gov/nist/nbis/nbis_v5_0_0.zip
unzip nbis_v5_0_0.zip
cd Rel_5.0.0

# Build and install
./setup.sh /usr/local/nbis --without-X11
make config
make it
sudo make install

# Add to PATH
echo 'export PATH=$PATH:/usr/local/nbis/bin' | sudo tee -a /etc/profile.d/nbis.sh
source /etc/profile.d/nbis.sh

# Verify
which mindtct
which bozorth3

echo "NBIS installed successfully!"