#!/bin/bash

# Check if the worker process is running
if pgrep -f "python app.py" > /dev/null; then
    exit 0
else
    exit 1
fi 