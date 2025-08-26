source $HOME/.cargo/env
python3 -m venv /workspace/venv
/workspace/venv/bin/pip install --upgrade pip setuptools wheel
/workspace/venv/bin/pip install TTS pyaudio