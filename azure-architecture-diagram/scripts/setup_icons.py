#!/usr/bin/env python3
"""
setup_icons.py — Download and cache official Microsoft Azure architecture icons.

Downloads the official icon set from Microsoft's CDN, extracts SVGs,
converts to PNG thumbnails using rsvg-convert, and builds an icon index.

Run once per session. Icons are cached in /home/claude/.azure-icons/

Usage:
    python3 setup_icons.py            # Download and cache all icons
    python3 setup_icons.py --list     # List available icon keys
"""

import os
import sys
import json
import subprocess
import zipfile
import shutil
from pathlib import Path

ICON_CACHE_DIR = Path("/home/claude/.azure-icons")
ICON_INDEX_FILE = ICON_CACHE_DIR / "index.json"
ICON_ZIP_URL = "https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V21.zip"
ICON_SIZE = 64  # px — rendered size for diagram compositing

# Mapping: friendly key → (svg filename substring, category)
# These are the most commonly used services in Azure Architecture Center diagrams
ICON_KEY_MAP = {
    # Analytics
    "data-factory":       ("Data-Factories", "analytics"),
    "synapse":            ("Azure-Synapse-Analytics", "analytics"),
    "stream-analytics":   ("Stream-Analytics-Jobs", "analytics"),
    "databricks":         ("Azure-Databricks", "analytics"),
    "power-bi":           ("Power-BI-Embedded", "analytics"),
    "event-hubs":         ("Event-Hubs.svg", "analytics"),
    "data-lake":          ("Data-Lake-Store-Gen1", "analytics"),
    # AI + Machine Learning
    "openai":             ("Azure-OpenAI", "ai"),
    "cognitive-search":   ("Cognitive-Search", "ai"),
    "cognitive-services":  ("10162-icon-service-Cognitive-Services.svg", "ai"),
    "machine-learning":   ("10166-icon-service-Machine-Learning.svg", "ai"),
    "speech":             ("Speech-Services", "ai"),
    "language":           ("02876-icon-service-Language.svg", "ai"),
    # Databases
    "sql-database":       ("SQL-Database.svg", "databases"),
    "cosmos-db":          ("Azure-Cosmos-DB", "databases"),
    "redis":              ("Cache-Redis", "databases"),
    "purview":            ("Purview-Accounts", "databases"),
    # Compute
    "app-service":        ("10035-icon-service-App-Services.svg", "compute"),
    "kubernetes":         ("Kubernetes-Services", "compute"),
    "function-app":       ("Function-Apps", "compute"),
    # Identity
    "entra-id":           ("Entra-ID-Protection", "identity"),
    "b2c":                ("Azure-AD-B2C", "identity"),
    "entra-connect":      ("02854-icon-service-Entra-Connect.svg", "identity"),
    # Security
    "key-vault":          ("Key-Vaults", "security"),
    "defender":           ("Microsoft-Defender-for-Cloud", "security"),
    # Networking
    "cdn":                ("CDN-Profiles.svg", "networking"),
    "api-management":     ("API-Management-Services", "devops"),
    "front-door":         ("Front-Door", "networking"),
    # Storage
    "storage-account":    ("Storage-Accounts.svg", "storage"),
    "data-share":         ("Data-Shares", "storage"),
    "blob":               ("Blob-Block", "storage"),
    # Management + Governance
    "monitor":            ("00001-icon-service-Monitor.svg", "monitor"),
    "app-insights":       ("Application-Insights", "monitor"),
    "cost-management":    ("Cost-Management.svg", "management"),
    "policy":             ("Policy.svg", "management"),
    # DevOps
    "devops":             ("Azure-DevOps.svg", "devops"),
    # Integration
    "service-bus":        ("Azure-Service-Bus", "integration"),
    # IoT
    "iot-hub":            ("IoT-Hub.svg", "iot"),
}


def ensure_rsvg():
    """Ensure rsvg-convert is available."""
    if shutil.which("rsvg-convert"):
        return True
    print("Installing librsvg2-bin for SVG→PNG conversion...")
    subprocess.run(["apt-get", "install", "-y", "-q", "librsvg2-bin"],
                   capture_output=True)
    return shutil.which("rsvg-convert") is not None


def download_icons():
    """Download official Azure icon ZIP from Microsoft CDN."""
    zip_path = ICON_CACHE_DIR / "azure-icons.zip"
    if zip_path.exists() and zip_path.stat().st_size > 100000:
        print(f"Icon ZIP already cached ({zip_path.stat().st_size:,} bytes)")
        return zip_path
    
    print(f"Downloading official Azure icons from Microsoft CDN...")
    result = subprocess.run(
        ["curl", "-sL", "-o", str(zip_path), ICON_ZIP_URL],
        capture_output=True, text=True
    )
    if zip_path.exists() and zip_path.stat().st_size > 100000:
        print(f"Downloaded {zip_path.stat().st_size:,} bytes")
        return zip_path
    else:
        print("WARNING: Download failed. Fallback icons will be used.")
        return None


def extract_and_index(zip_path):
    """Extract SVGs and build icon index."""
    svg_dir = ICON_CACHE_DIR / "svg"
    svg_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        svg_files = [f for f in zf.namelist() if f.endswith('.svg')]
        for svg_file in svg_files:
            # Flatten into svg/ directory
            fname = os.path.basename(svg_file)
            target = svg_dir / fname
            if not target.exists():
                with zf.open(svg_file) as src, open(target, 'wb') as dst:
                    dst.write(src.read())
    
    svg_count = len(list(svg_dir.glob("*.svg")))
    print(f"Extracted {svg_count} SVG icons")
    return svg_dir


def resolve_icon(key, svg_dir):
    """Find the SVG file matching an icon key."""
    if key not in ICON_KEY_MAP:
        return None
    
    pattern = ICON_KEY_MAP[key][0]
    
    # If pattern is an exact filename, use it directly
    exact = svg_dir / pattern
    if exact.exists():
        return exact
    
    # Otherwise search by substring
    for svg_file in sorted(svg_dir.glob("*.svg")):
        if pattern in svg_file.name:
            return svg_file
    
    return None


def convert_to_png(svg_path, png_path, size=ICON_SIZE):
    """Convert SVG to PNG using rsvg-convert."""
    result = subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size),
         str(svg_path), "-o", str(png_path)],
        capture_output=True, text=True
    )
    return png_path.exists()


def setup(force=False):
    """Main setup: download, extract, convert, index."""
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    png_dir = ICON_CACHE_DIR / "png"
    png_dir.mkdir(exist_ok=True)
    
    # Check if already done
    if not force and ICON_INDEX_FILE.exists():
        with open(ICON_INDEX_FILE) as f:
            index = json.load(f)
        available = sum(1 for v in index.values() if v)
        print(f"Icon cache ready: {available}/{len(ICON_KEY_MAP)} icons available")
        return index
    
    if not ensure_rsvg():
        print("WARNING: rsvg-convert not available. Using fallback icons.")
        return {}
    
    zip_path = download_icons()
    if not zip_path:
        return {}
    
    svg_dir = extract_and_index(zip_path)
    
    # Convert each mapped icon to PNG
    index = {}
    for key in ICON_KEY_MAP:
        svg_file = resolve_icon(key, svg_dir)
        if svg_file:
            png_file = png_dir / f"{key}.png"
            if not png_file.exists() or force:
                convert_to_png(svg_file, png_file)
            if png_file.exists():
                index[key] = str(png_file)
            else:
                index[key] = None
        else:
            index[key] = None
    
    # Save index
    with open(ICON_INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)
    
    available = sum(1 for v in index.values() if v)
    print(f"Icon setup complete: {available}/{len(ICON_KEY_MAP)} icons converted")
    return index


def list_icons():
    """List all available icon keys."""
    if ICON_INDEX_FILE.exists():
        with open(ICON_INDEX_FILE) as f:
            index = json.load(f)
        for key, path in sorted(index.items()):
            status = "✓" if path else "✗"
            category = ICON_KEY_MAP.get(key, ("", "unknown"))[1]
            print(f"  {status} {key:25s} [{category}]")
    else:
        print("Run setup first: python3 setup_icons.py")


if __name__ == "__main__":
    if "--list" in sys.argv:
        list_icons()
    else:
        setup(force="--force" in sys.argv)
