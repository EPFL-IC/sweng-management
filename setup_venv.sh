#!/bin/bash
#
# Copyright 2015 Google Inc.
# Author: Stefan Bucur (sbucur@google.com)

set -e

official_name=official
official_repo="https://github.com/EPFL-IC/sweng-management"
if ! git remote show "$official_name" &>/dev/null; then
    git remote add "$official_name" "$official_repo"
    git fetch "$official_name"
fi

# Temporarily download Virtualenv's source code
mkdir virtualenv
curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.1.2.tar.gz | tar -xz -C virtualenv --strip-components=1

# Create our virtual environment, called "venv"
python virtualenv/virtualenv.py venv

# Remove Virtualenv's source code
rm -rf virtualenv

# Setup "venv"
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
deactivate
