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

## 音声エージェント統合システム

現在の実装では以下のコンポーネントが統合されています:

### メイン実行
- `src/app.py`: 統合音声エージェントのメイン実行ファイル
- `python -m src.app` で起動

### 音声処理パイプライン
1. **音声キャプチャ** (`src/audio/capture.py`): マイクからの音声入力
2. **Wake Word検出 + VAD** (`src/audio/wake_vad.py`): OpenWakeWordとWebRTC VADによる音声検知
3. **音声認識** (`src/audio/asr.py`): faster-whisperによる文字起こし
4. **言語モデル処理** (`src/nlp/llm.py`, `src/nlp/agent.py`): LLM推論とツール連携
5. **音声合成** (`src/io/voicevox_tts.py`): VOICEVOXによるTTS出力

### 重要な実装上の注意点

#### 音声エコー対策
TTS出力音声が入力として検知される問題を解決するため、以下の機能を実装:

1. **音声処理の一時停止/再開機能** (`src/audio/wake_vad.py:118-133`)
   - `pause()`: TTS再生中は音声入力を停止
   - `resume()`: TTS終了後に音声入力を再開し、強制的にwake word待機状態にリセット

2. **動的閾値調整とクールダウン機能** (`src/audio/wake_vad.py:83-96`)
   - 通常時: wake word検知閾値 0.3
   - クールダウン中（TTS終了後2秒間）: 閾値 0.5 でTTS音声残響による誤検知を防止

3. **状態管理の強制リセット** (`src/audio/wake_vad.py:126-132`)
   - TTS後は`is_awake=False`、`speech_detected=False`に強制リセット
   - バッファクリアと無音カウンタリセット

#### 設定ファイル
- `config/config.yaml`: 全コンポーネントの設定
- Wake Word: "alexa" または "jarvis" (OpenWakeWordモデル使用)
- VAD aggressiveness: 2 (0-3の範囲)
- VOICEVOX TTS: ずんだもん（speaker_id: 3）

## 開発コマンド

```bash
# 依存関係のインストール/同期
uv sync

# 新しいパッケージの追加 (uv が適切なバージョンを判断)
uv add <package-name>

# 統合音声エージェント実行
python -m src.app

# 音声認識サンプル実行
python src/whisper-sample.py

# 言語モデルサンプル実行
python src/llama-sample.py
```

## トラブルシューティング

### 音声エコー問題
症状: TTS出力後にwake wordなしで反応してしまう
対策: 上記のエコー対策機能により解決済み

### VOICEVOX接続問題
症状: VOICEVOX Engineに接続できない
対策: `http://127.0.0.1:50021` でVOICEVOX Engineが起動していることを確認

## 注意事項

- Python 3.13 との互換性のため pyproject.toml で管理
- パッケージ追加時は直接編集ではなく `uv add` を使用すること
- macOS で PyAudio を使用する場合は事前に `brew install portaudio` が必要
- VOICEVOX Engineの事前起動が必要