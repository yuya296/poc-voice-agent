#!/usr/bin/env python3
"""
音声入力のテストスクリプト
macOSでマイクが使用できるかチェック
"""
import sounddevice as sd
import numpy as np
import time

def test_audio():
    print("=== 音声デバイステスト ===")
    
    # 利用可能なデバイスを表示
    print("\n利用可能なオーディオデバイス:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # 入力デバイスのみ
            print(f"  {i}: {device['name']} (入力チャンネル: {device['max_input_channels']})")
    
    # デフォルトデバイスを取得
    default_device = sd.query_devices(kind='input')
    print(f"\nデフォルト入力デバイス: {default_device['name']}")
    
    # MacBook Air Microphoneを指定してテスト
    macbook_device = None
    for i, device in enumerate(devices):
        if 'MacBook Air Microphone' in device['name']:
            macbook_device = i
            break
    
    if macbook_device is not None:
        print(f"\nMacBook Air Microphone (デバイス {macbook_device}) でテストします...")
    else:
        print(f"\nデフォルトデバイス ({default_device['name']}) でテストします...")
    
    # 5秒間音声をキャプチャしてレベルをモニタ
    print("5秒間音声レベルをモニタします（何か話してください）...")
    
    def audio_callback(indata, frames, time, status):
        if status:
            print(f"\nオーディオエラー: {status}")
        
        # RMSレベル計算
        rms = np.sqrt(np.mean(indata ** 2))
        # バーで視覚化
        bar_length = int(rms * 100)
        bar = '█' * min(bar_length, 50)
        print(f"\rRMS: {rms:.4f} |{bar:<50}|", end='', flush=True)
    
    try:
        with sd.InputStream(
            device=macbook_device if macbook_device is not None else None,
            samplerate=16000,
            channels=1,
            dtype=np.float32,
            blocksize=320,  # 20ms
            callback=audio_callback
        ):
            time.sleep(5)
            
        print("\n\n音声テスト完了!")
        
    except Exception as e:
        print(f"\n音声キャプチャエラー: {e}")
        print("\nmacOSの場合、システム環境設定 > セキュリティとプライバシー > マイクで")
        print("Terminalまたはこのアプリケーションにマイクの使用を許可してください")

if __name__ == "__main__":
    test_audio()