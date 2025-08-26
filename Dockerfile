# ベースイメージ（Bookworm + Python 3.11）
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# 環境変数
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/workspace/venv/bin:$PATH"

# 必要パッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Rust インストール
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 仮想環境作成
RUN python3 -m venv /workspace/venv

# pip / setuptools / wheel 更新
RUN /workspace/venv/bin/pip install --upgrade pip setuptools wheel

# Debian/Bookworm 系
RUN apt-get update && \
    apt-get install -y portaudio19-dev && \
    rm -rf /var/lib/apt/lists/*

# その後に Python パッケージをインストール
RUN /workspace/venv/bin/pip install TTS pyaudio

# 作業ディレクトリ
WORKDIR /workspace

# デフォルトのシェルで venv 有効化
SHELL ["/bin/bash", "-c", "source /workspace/venv/bin/activate && exec bash"]
