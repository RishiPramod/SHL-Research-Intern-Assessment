#!/usr/bin/env python3
"""
Startup script that reads PORT from environment and runs uvicorn.
This is an alternative to start.sh for platforms that prefer Python.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port)
