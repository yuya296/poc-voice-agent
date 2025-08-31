# CLAUDE.md

このファイルはClaude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## 開発環境

Python ベースの音声エージェント POC プロジェクトです。macOS ローカルまたは devcontainer で実行できます。

### 開発セットアップ

**初期セットアップ (macOS のみ):**
```bash
brew install portaudio
```

### Python 環境

- devcontainer では Python 3.11、ローカルでは Python 3.13+ を使用
- 依存関係は `pyproject.toml` で管理
- **パッケージ管理には uv を使用**
- 新しいパッケージの追加: `uv add <package-name>` (uv が適切なバージョンを判断)
- 直接 pyproject.toml を編集せず、必ず `uv add` コマンドを使用すること

## プロジェクト構成

音声エージェント POC の主要コンポーネント:

### 音声認識 (Whisper)
- `src/whisper-sample.py` に配置
- `faster-whisper` ライブラリを使用
- 複数のモデルサイズをサポート (tiny/base/small/medium/large) - 日本語には small 以上を推奨
- CPU 推論、int8 量子化で設定
- `resource/` ディレクトリの音声ファイルを処理

### 言語モデル (LLM)
- `src/llama-sample.py` に配置
- HuggingFace Transformers と OpenLLaMA モデルを使用
- メモリ効率のための 4bit 量子化をサポート
- CUDA 推論で設定

## 主要な依存関係

- **音声処理**: sounddevice, faster-whisper
- **ML/AI**: transformers, torch, torchaudio, sentencepiece
- **音声ライブラリ**: librosa, soundfile
- **その他**: numpy, pandas, scipy, requests

## 開発コマンド

```bash
# 依存関係のインストール/同期
uv sync

# 新しいパッケージの追加 (uv が適切なバージョンを判断)
uv add <package-name>

# 音声認識サンプル実行
python src/whisper-sample.py

# 言語モデルサンプル実行
python src/llama-sample.py
```

## 注意事項

- Python 3.13 との互換性のため pyproject.toml で管理
- パッケージ追加時は直接編集ではなく `uv add` を使用すること
- macOS で PyAudio を使用する場合は事前に `brew install portaudio` が必要