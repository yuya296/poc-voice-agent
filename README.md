# POC Voice Agent

完全ローカルで動作する音声エージェントのPoC実装です。

## 機能

- Wake Word検出（"hey nova"）
- 音声認識（faster-whisper）
- ローカルLLM（llama-cpp-python）
- 音声合成（VOICEVOX）
- ツール統合（時計、IoTモック）

## セットアップ

### 1. 依存関係のインストール

```bash
# PortAudioのインストール（macOS）
brew install portaudio

# Pythonパッケージのインストール
uv sync
```

### 2. モデルファイルの準備

#### Whisper（音声認識）
```bash
# 自動ダウンロードされるため手動設定不要
# 初回実行時にモデルが自動的にダウンロードされます
```

#### LLM（言語モデル）
```bash
# Hugging Face からGGUFモデルをダウンロード
mkdir -p models/llm

# 例: TinyLlama 1.1B
wget -O models/llm/tinyllama-1.1b-chat-q4_K_M.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.q4_K_M.gguf
```

#### VOICEVOX TTS（音声合成）
```bash
# VOICEVOX Engineをダウンロード・起動
# 公式サイト: https://voicevox.hiroshiba.jp/

# macOSの場合:
# 1. 公式サイトからVOICEVOX Engineをダウンロード
# 2. アプリケーションを起動（http://127.0.0.1:50021 でサーバーが開始）
# 3. ブラウザで http://127.0.0.1:50021/docs にアクセスして動作確認

# または、Dockerで起動（推奨）:
docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

## 実行

```bash
uv run python -m src.app
```

## 設定

`config/config.yaml` で各種設定を変更できます：

- 音声デバイス
- モデルパス
- LLMパラメータ
- ツール有効/無効

## 使用方法

1. アプリケーションを起動
2. "hey nova"と話しかける（Wake Word）
3. 質問や指示を話す
4. エージェントが音声で応答

## サポートされるコマンド例

- "今何時？" → 時計ツールで現在時刻を回答
- "電気をつけて" → IoTモックでデバイス制御をシミュレート

## トラブルシューティング

### モデルが見つからない
- `config/config.yaml`のパスを確認
- モデルファイルが正しい場所に配置されているか確認

### 音声が聞こえない
- `config/config.yaml`のaudio.deviceを確認
- macOSの場合、システム環境設定でマイクの許可を確認

### Piperが動かない
- `piper --version`でPiperがインストールされているか確認
- 音声モデルファイル（model.onnx, model.json）が正しく配置されているか確認
