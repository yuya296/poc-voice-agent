# POC Voice Agent

## devcontainer起動手順(for MacOS)

### 初回のみセットアップ

```bash
brew install pulseaudio
```

### 起動手順

以下で PulseAudio を起動した後に、 devcontainer を起動する。

```bash
pulseaudio --load="module-native-protocol-tcp" --exit-idle-time=-1 -vvvv
```