#!/usr/bin/env python
# coding: utf-8

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# The parent directory containing your topics and discussions
DATA_DIR = Path("data")

# Serve the actual markdown files and images statically
app.mount("/data", StaticFiles(directory="data"), name="data")
# Serve the frontend HTML/JS statically
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    """Serve the homepage dashboard."""
    return FileResponse("static/index.html")

@app.get("/viewer")
def read_viewer():
    """Serve the markdown viewer page."""
    return FileResponse("static/question.html")

@app.get("/api/tree")
def get_tree():
    """Recursively scan the data directory and return a JSON tree."""
    if not DATA_DIR.exists():
        return {"error": "Data directory not found."}

    def build_tree(current_path):
        tree = {
            "name": current_path.name,
            "path": str(current_path.relative_to(DATA_DIR)) if current_path != DATA_DIR else "",
            "dirs": [],
            "files": []
        }
        
        for item in sorted(current_path.iterdir()):
            if item.is_dir():
                tree["dirs"].append(build_tree(item))
            # Only index .md files starting with "q"
            elif item.suffix == ".md" and item.name.lower().startswith("q"):
                tree["files"].append({
                    "name": item.name,
                    "path": str(item.relative_to(DATA_DIR)).replace("\\", "/")
                })
        return tree
        
    return build_tree(DATA_DIR)

# Add this new endpoint to your main.py
@app.get("/api/related_images")
def get_related_images(file: str):
    """Find images related to a specific markdown file based on its prefix."""
    file_path = DATA_DIR / file
    
    # If the file doesn't exist, return an empty list
    if not file_path.exists() or not file_path.is_file():
        return {"images": []}
    
    directory = file_path.parent
    base_name = file_path.name
    
    # Extract the prefix (e.g., "q1_" from "q1_abc.md")
    # If there is no underscore, it uses the filename without extension + "_"
    if '_' in base_name:
        prefix = base_name.split('_')[0] + '_'
    else:
        prefix = file_path.stem + '_'

    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    related_images = []
    
    # Scan the directory for images starting with the same prefix
    for item in directory.iterdir():
        if item.is_file() and item.suffix.lower() in valid_extensions:
            if item.name.lower().startswith(prefix.lower()):
                # Create a relative URL for the frontend to load the image
                rel_path = str(item.relative_to(DATA_DIR)).replace("\\", "/")
                related_images.append(f"/data/{rel_path}")
                
    return {"images": sorted(related_images)}

import uvicorn

if __name__ == "__main__":
    # Run the uvicorn server programmatically
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)    
