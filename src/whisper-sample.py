from faster_whisper import WhisperModel

# tiny/base/small/medium/large がある。日本語なら small 以上が良い。
model_size = "small"

# CPUモードで実行（ラズパイ）
model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("resource/hello.wav", beam_size=5)

print("Detected language '%s' with probability %.2f" %
      (info.language, info.language_probability))

for segment in segments:
    print("[%0.2fs -> %0.2fs] %s" % (segment.start, segment.end, segment.text))
