# 全体アーキテクチャ（PoC・完全ローカル）

```
[Mic] → [Wake Word+VAD] → [ASR(Faster-Whisper)] → [Agent(Core)]
                                    │                ├─ [Tool Registry (MCP互換IF)]
                                    │                ├─ [LLM(local: llama-cpp-python)]
                                    └→ [Partial transcripts bus]  └─ [Policy/Router(将来:Cloud fallback)]
                                        │
[Sentence Chunker] → [TTS(Piper)] → [Speaker]   ※LLM出力は文単位でTTSに即流す（準ストリーミング）
```

* **Wake Word + VAD**: openwakeword + WebRTC VADで低遅延検出＆区間切り出し
* **ASR**: faster-whisper（Python API、CT2バックエンド）
* **Agent**: ReAct系の最小プランナ（Python）＋簡易ツール呼び出し
* **LLM**: `llama-cpp-python` で GGUF 量子化モデル（1〜2B級、q4\_K\_M）
* **TTS**: Piper（Pythonラッパ or サブプロセス）でja-JP音声

> PoCは**完全オフライン**。Routerは将来のクラウドfallback用の抽象だけ用意。

---

## 技術選定の理由

* **uv**: 超高速・ロックファイル込み、Piでも軽い。再現性と起動速度◎
* **faster-whisper**: Piでもsmall/tinyでリアルタイム近く可。VAD連携が容易
* **llama-cpp-python**: C++コアだがPythonから操作。PiでのCPU/GGML/GGUF推論の事実上の定番
* **Piper**: オフライン日英など多言語TTS。軽量・高品質でラズパイ適性が高い
* **openwakeword + webrtcvad**: OSSで配布容易。誤起動抑制と低遅延

---

## リポジトリ構成（uv前提・単一プロセス/モジュール）

```
voice-agent/
├─ pyproject.toml
├─ uv.lock
├─ src/
│  ├─ app.py                  # エントリポイント
│  ├─ core/
│  │  ├─ bus.py               # 非同期イベントバス（asyncio.Queue）
│  │  ├─ config.py            # 設定読込（YAML/ENV）
│  │  ├─ logging.py           # 構造化ログ
│  ├─ audio/
│  │  ├─ capture.py           # sounddeviceでマイク入力、リングバッファ
│  │  ├─ wake_vad.py          # openwakeword + webrtcvad
│  │  ├─ asr.py               # faster-whisperラッパ（チャンク処理）
│  ├─ nlp/
│  │  ├─ llm.py               # llama-cpp-pythonストリーム生成
│  │  ├─ agent.py             # ReAct最小実装（ツール呼出し・プロンプト）
│  │  ├─ splitter.py          # 文分割（句読点/中黒/読点で即時フラッシュ）
│  ├─ io/
│  │  ├─ tts.py               # Piper統合（ストリーミング風に文毎合成）
│  ├─ tools/
│  │  ├─ base.py              # MCP互換IF: name, schema, run()
│  │  ├─ clock.py             # サンプル：時刻応答（完全ローカル）
│  │  ├─ iot_mock.py          # サンプル：ライトON/OFFの擬似
│  ├─ ui/
│  │  └─ cli.py               # CLI/ホットキー/状態表示
│  └─ server/
│     └─ rpc.py               # 将来用: WebSocket/gRPC（今は未使用 or オフ）
├─ models/
│  ├─ whisper/…               # whisper small/tiny（.bin or ct2自動DLキャッシュ）
│  ├─ llm/…                   # TinyLlama/Phi派生 GGUF (q4_K_M)
│  └─ piper/ja-JP-voice/…     # piperのja-JP音声(onnx+json)
├─ config/
│  ├─ config.yaml
│  └─ prompts/
│     └─ system_ja.txt
└─ scripts/
   ├─ install_models.sh       # 音声/LLM/TTSモデルDL（対話式/サイズ選択）
   └─ run.sh
```

---

## 主要データフロー（低レイテンシ最適化）

1. **audio.capture** が16kHz monoでリングバッファ供給（frame=20ms）
2. **wake\_vad** が wakeword 検出→音声区間（VAD）を `asr` へ流す
3. **asr** が 0.5〜1.0秒ごとに部分文字起こしを更新（最終化時に確定）
4. **agent** は確定テキスト受領後に LLM 生成を開始
5. **splitter** が LLMのトークンストリームを「。」等で文に切って **tts** へ即渡す
6. **tts** は文毎に合成→スピーカー再生（先頭文は最速出し）

> 「超速」体感のカギ：**入力はVADで短尺化**、**出力は文単位で即TTS**。

---

## 設定ファイル例（`config/config.yaml`）

```yaml
audio:
  device: null          # 既定 or arecord/sounddeviceで列挙名
  rate: 16000
  chunk_ms: 20
  pre_roll_ms: 300      # 発話頭切れ対策
wake:
  model_path: models/openwakeword/hey_nova.tflite
  keyword: "hey nova"   # 任意。将来カスタム学習可
vad:
  aggressiveness: 2     # 0-3
asr:
  model_size: small     # tiny/small
  compute_type: int8
  beam_size: 1
  vad_filter: true
llm:
  gguf_path: models/llm/tinyllama-1.1b-chat-q4_K_M.gguf
  ctx_size: 2048
  n_threads: 4
  n_gpu_layers: 0       # Piは0推奨
  top_p: 0.9
  top_k: 40
  temp: 0.7
  max_tokens: 256
agent:
  tools_enabled: [clock, iot_mock]
  system_prompt_path: config/prompts/system_ja.txt
tts:
  piper_bin: piper      # PATHにある場合はそのまま
  voice_dir: models/piper/ja-JP-voice
  sentence_pause_ms: 120
logging:
  level: INFO
  json: false
privacy:
  save_audio: false
  save_text: true      # デバッグ用ログ（後でfalse推奨）
```

---

## 依存・セットアップ（uv）

```bash
# プロジェクト初期化
uv init voice-agent && cd voice-agent
uv python pin 3.11

# 主要パッケージ
uv add sounddevice webrtcvad numpy pyyaml pydantic loguru rich
uv add faster-whisper==1.*                # ASR
uv add llama-cpp-python                   # LLM
uv add openwakeword                       # Wake word
uv add piper-tts orjson                   # TTSラッパ（実行はpiperバイナリでも可）

# 実行
uv run python -m src.app
```

> **Piper音声モデル**はGitHubリリース等から`models/piper/ja-JP-voice/`へ配置（`.onnx`と`model.json`）。
> **LLM GGUF**はTinyLlama 1.1Bなど小型を推奨（q4\_K\_M）。Piでの体感を優先。

---

## 重要クラスのインタフェース（抜粋）

### イベントバス（`core/bus.py`）

```python
class Event(NamedTuple):
  type: str
  payload: dict

class Bus:
  def __init__(self): self.q = asyncio.Queue()
  async def publish(self, e: Event): await self.q.put(e)
  async def subscribe(self): 
      while True: yield await self.q.get()
```

### ASRラッパ（`audio/asr.py`）

```python
class ASR:
  def __init__(self, cfg): self.model = WhisperModel(cfg.model_size, compute_type=cfg.compute_type)
  async def transcribe_segments(self, pcm_iter) -> AsyncIterator[str]:
      # VAD済みPCMを受け取り、確定文字列をyield
      ...
```

### Agent（`nlp/agent.py`）

```python
class Tool(Protocol):
  name: str
  description: str
  schema: dict
  async def run(self, **kwargs) -> str: ...

class Agent:
  def __init__(self, llm, tools: dict[str, Tool], system_prompt: str): ...
  async def handle(self, user_text: str) -> AsyncIterator[str]:
      # ReAct最小: 思考は隠し、関数呼び出し風のJSONを正規表現で抽出→Tool実行→結果をLLMへフィード
      # 逐次トークンをyield（splitterが文単位に束ねる）
      ...
```

### LLM（`nlp/llm.py`）

```python
from llama_cpp import Llama

class LocalLLM:
  def __init__(self, gguf_path, **params):
     self.llm = Llama(model_path=gguf_path, n_ctx=params['ctx_size'], n_threads=params['n_threads'], n_gpu_layers=params['n_gpu_layers'])

  def stream(self, prompt: str) -> Iterator[str]:
     for out in self.llm.create_completion(prompt, stream=True, temperature=..., top_p=..., max_tokens=...):
        yield out["choices"][0]["text"]
```

### TTS（`io/tts.py`）

```python
class PiperTTS:
  def __init__(self, bin_path, voice_dir): ...
  async def speak_sentences(self, sentences: AsyncIterator[str]):
      # 文が来るたびにpiperへstdinで渡し、wavをパイプでaplayへ
      ...
```

---

## プロンプト方針（`config/prompts/system_ja.txt`）

* 家庭向け・丁寧すぎず親しみのある口調
* ツール呼び出しは明示的トリガ（例：「\<tool\:clock time=now>」といった簡易タグ）
* 出力は**短文の連なり**を推奨（TTSの文切りに最適）

---

## 性能目標（ラズパイ8GB）

* **起動**: < 5s（モデルロード除く）
* **ウェイク→ASR確定**: 0.6–1.0s（発話長による）
* **LLM初回トークン**: 0.3–1.0s（1–2B, q4\_K\_M, n\_threads=4）
* **TTS先頭音**: 文1到着から < 300ms

※ 実測で遅い場合：

* LLMをさらに小型化（`q5_0`→`q4_K_M`/`q3_K_M`）、max\_tokens短縮
* ASRを`tiny`、beam=1固定、VADアグレッシブ化
* 文閾値を短めに（句点待たず読点や「ね/よ/です」で切る）

---

## エラーハンドリングと回復

* **音声I/O**: デバイス未検出→リトライ＆別デバイス候補をログ提示
* **ASR/LLM/TTS**: 例外捕捉→「聞き取りに失敗しました」等の短い代替音声
* **モデル不在**: 起動時チェック→不足モデルをダウンロードする`install_models.sh`をガイド
* **監視**: 心拍ログ（30s）・CPU温度警告・長時間連続処理でスロットリング

---

## セキュリティ/プライバシー

* 既定で**音声を保存しない**
* テキストログは開発中のみ（オフにできる）
* 将来のクラウド接続時はプロンプト内にPIIを入れないポリシー＋マスキング

---

## ローカル実行コマンド

```bash
# 1) モデル配置（初回のみ）
bash scripts/install_models.sh      # 対話でASR/LLM/TTS選択DL

# 2) 起動
uv run python -m src.app

# 3) デバッグ
uv run python -m src.ui.cli --list-audio
uv run python -m src.tools.iot_mock --demo
```

---

## 将来拡張（製品版への橋渡し）

* **Router実装**：local→cloud切替（遅延/長さ/信頼度で動的判定）
* **MCP実体**：いまのTool IFをMCP準拠へ（JSON-RPC over WebSocket）
* **設定UI**：LAN内WebUIでマイク/音声/モデル選択・ネットワーク設定
* **常駐化**：systemd unit（自動再起動・ログローテ）

---

## 最小サンプル：エントリ起動（概略）

```python
# src/app.py
import asyncio
from core.config import load_config
from audio.capture import AudioCapture
from audio.wake_vad import WakeAndVAD
from audio.asr import ASR
from nlp.llm import LocalLLM
from nlp.agent import Agent
from nlp.splitter import sentence_stream
from io.tts import PiperTTS
from tools import clock, iot_mock

async def main():
    cfg = load_config("config/config.yaml")

    cap = AudioCapture(cfg.audio)
    wv  = WakeAndVAD(cfg.wake, cfg.vad)
    asr = ASR(cfg.asr)
    llm = LocalLLM(**cfg.llm)
    tts = PiperTTS(cfg.tts)

    tools = {t.name: t for t in [clock.ClockTool(), iot_mock.IoTMockTool()]}

    agent = Agent(llm=llm, tools=tools, system_prompt=open(cfg.agent.system_prompt_path).read())

    async for utter_pcm in wv.iter_utterances(cap.stream()):
        text = await asr.transcribe(utter_pcm)
        if not text.strip(): continue
        token_iter = agent.handle(text)                # Async token stream
        sent_iter  = sentence_stream(token_iter)       # 文単位に整形
        await tts.speak_sentences(sent_iter)           # 文ごとに即再生

if __name__ == "__main__":
    asyncio.run(main())
```