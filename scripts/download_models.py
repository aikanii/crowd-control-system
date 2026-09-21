#!/usr/bin/env python3
"""
Download MobileNet SSD models
"""
import os
import sys
import urllib.request

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

URLS = {
    "MobileNetSSD_deploy.prototxt": "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.prototxt",
    "MobileNetSSD_deploy.caffemodel": "https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.caffemodel"
}

# Alternative mirror for caffemodel via opencv extra?
ALT_URLS = {
    "MobileNetSSD_deploy.caffemodel": [
        "https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.caffemodel",
        "https://drive.google.com/uc?export=download&id=0B3gersZ2cHIxRm5PMWRoTkdHd3U"  # may not work
    ]
}

def download(url, dest):
    print(f"Downloading {url} -> {dest}")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"Saved {dest} ({os.path.getsize(dest)} bytes)")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

def main():
    for name, url in URLS.items():
        dest = os.path.join(MODELS_DIR, name)
        if os.path.exists(dest):
            print(f"Already exists: {dest}, skipping")
            continue
        success = download(url, dest)
        if not success and name in ALT_URLS:
            for alt in ALT_URLS[name]:
                if alt == url:
                    continue
                if download(alt, dest):
                    break

    print(f"\nModels in {MODELS_DIR}:")
    for f in os.listdir(MODELS_DIR):
        print(f" - {f}")

if __name__ == "__main__":
    main()
