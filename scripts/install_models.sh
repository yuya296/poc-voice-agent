#!/bin/bash

echo "Voice Agent - モデルインストールスクリプト"
echo "==========================================="

# 基本ディレクトリ作成
mkdir -p models/{whisper,llm,piper/ja-JP-voice}

# LLMモデルのダウンロード
echo "1. LLMモデルのダウンロード"
echo "利用可能なモデル:"
echo "  1) TinyLlama 1.1B (軽量、推奨)"
echo "  2) Phi-2 2.7B (高品質、メモリ多め)"
echo "  3) スキップ"

read -p "選択してください [1-3]: " llm_choice

case $llm_choice in
    1)
        echo "TinyLlama 1.1B をダウンロード中..."
        wget -O models/llm/tinyllama-1.1b-chat-q4_K_M.gguf \
            https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.q4_K_M.gguf
        ;;
    2)
        echo "Phi-2 2.7B をダウンロード中..."
        wget -O models/llm/phi-2-q4_K_M.gguf \
            https://huggingface.co/microsoft/phi-2-gguf/resolve/main/phi-2.q4_K_M.gguf
        ;;
    3)
        echo "LLMモデルをスキップしました"
        ;;
    *)
        echo "無効な選択です。スキップします。"
        ;;
esac

# TTSモデルのダウンロード
echo ""
echo "2. Piper TTS 日本語音声モデルのダウンロード"
echo "利用可能な音声:"
echo "  1) haruka (女性、推奨)"
echo "  2) takumi (男性)"
echo "  3) スキップ"

read -p "選択してください [1-3]: " tts_choice

case $tts_choice in
    1)
        echo "haruka (女性音声) をダウンロード中..."
        cd models/piper/ja-JP-voice
        wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ja/ja_JP/haruka/medium/ja_JP-haruka-medium.onnx
        wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ja/ja_JP/haruka/medium/ja_JP-haruka-medium.onnx.json
        mv ja_JP-haruka-medium.onnx model.onnx
        mv ja_JP-haruka-medium.onnx.json model.json
        cd ../../..
        ;;
    2)
        echo "takumi (男性音声) をダウンロード中..."
        cd models/piper/ja-JP-voice
        wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ja/ja_JP/takumi/medium/ja_JP-takumi-medium.onnx
        wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ja/ja_JP/takumi/medium/ja_JP-takumi-medium.onnx.json
        mv ja_JP-takumi-medium.onnx model.onnx
        mv ja_JP-takumi-medium.onnx.json model.json
        cd ../../..
        ;;
    3)
        echo "TTSモデルをスキップしました"
        ;;
    *)
        echo "無効な選択です。スキップします。"
        ;;
esac

# Piperバイナリのチェック
echo ""
echo "3. Piper TTS バイナリのチェック"
if command -v piper &> /dev/null; then
    echo "✓ Piper TTS がインストールされています: $(piper --version)"
else
    echo "⚠ Piper TTS がインストールされていません"
    echo "以下のコマンドでインストールしてください:"
    echo "  brew install piper-tts"
    echo "または、https://github.com/rhasspy/piper/releases からダウンロード"
fi

echo ""
echo "モデルインストール完了!"
echo ""
echo "次の手順:"
echo "1. config/config.yaml でモデルパスを確認"
echo "2. uv run python -m src.app で実行"