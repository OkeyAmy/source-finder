"""
Entry script for running the SourceFinder API.
"""

import uvicorn

if __name__ == "__main__":
    print("Starting SourceFinder API...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 