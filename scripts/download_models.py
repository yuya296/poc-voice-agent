#!/usr/bin/env python3
"""
音声エージェント用モデルダウンロードスクリプト
"""
import os
import sys
from pathlib import Path
import requests
from urllib.parse import urlparse
from tqdm import tqdm
import yaml

def download_file(url: str, filepath: Path, description: str = ""):
    """ファイルをダウンロード"""
    print(f"Downloading {description}: {url}")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'wb') as f, tqdm(
        desc=description,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))
    
    print(f"✓ Downloaded: {filepath}")

def main():
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models"
    
    # 設定ファイル読み込み
    config_path = project_root / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("🤖 Voice Agent Model Downloader")
    print(f"Models will be downloaded to: {models_dir}")
    
    # ダウンロード対象モデル
    models_to_download = [
        {
            "name": "LLM Model (Phi-3.5 Mini Q4)",
            "url": "https://huggingface.co/microsoft/Phi-3.5-mini-instruct-gguf/resolve/main/Phi-3.5-mini-instruct-q4_k_m.gguf",
            "path": models_dir / "llm" / "phi-3.5-mini-q4_k_m.gguf"
        },
        {
            "name": "OpenWakeWord - Alexa",
            "url": "https://github.com/dscripka/openWakeWord/raw/main/openwakeword/resources/models/alexa_v0.1.onnx",
            "path": models_dir / "openwakeword" / "alexa_v0.1.onnx"
        },
        {
            "name": "OpenWakeWord - Hey Jarvis",
            "url": "https://github.com/dscripka/openWakeWord/raw/main/openwakeword/resources/models/hey_jarvis_v0.1.onnx",
            "path": models_dir / "openwakeword" / "hey_jarvis_v0.1.onnx"
        }
    ]
    
    for model in models_to_download:
        if model["path"].exists():
            print(f"⏭️  Skip (already exists): {model['name']}")
            continue
        
        try:
            download_file(model["url"], model["path"], model["name"])
        except Exception as e:
            print(f"❌ Failed to download {model['name']}: {e}")
            continue
    
    print("\n✅ Model download completed!")
    print("\n📋 Next steps:")
    print("1. Start VOICEVOX Engine: http://127.0.0.1:50021")
    print("2. Run voice agent: python -m src.app")
    
    # 設定ファイルの更新が必要かチェック
    llm_path = models_dir / "llm" / "phi-3.5-mini-q4_k_m.gguf"
    if llm_path.exists() and config['llm']['gguf_path'] != str(llm_path):
        print(f"\n⚠️  Update config/config.yaml:")
        print(f"   llm.gguf_path: {llm_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)