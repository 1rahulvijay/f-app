#!/bin/bash

Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Run the Flask app
exec python app.py
