# spider-docker

KingSpider / shin-spider (ROS1 Noetic) を Docker で動かす環境。最大 3 台、1 台 = パッド 1 つ。
パッドは Logicool F310 を **XInput モード (背面スイッチ X)** にしてください。

使えるロボットは `robots.yaml` に並べ、起動時に `KING=台数 SHIN=台数` で選びます(合計 1〜3 台)。

## Docker のセットアップ
- Ubuntu: Docker Engine + compose plugin (`sudo usermod -aG docker $USER` 後に再ログイン)
- Windows: Docker Desktop (WSL2 バックエンド)、`usbipd-win`、PowerShell

## Ubuntu
```bash
make build          # 初回のみ
make serial-list                 # 接続中のシリアルを一覧
make serial-set                  # 一覧から選んで robots.yaml の serial を書き換え (ROBOT=king1 で 1 台だけ)
make up KING=1 SHIN=2            # 台数を指定して起動 (動作確認。実機なし)
make up KING=1 DRY_RUN=0         # 実機 (/dev/input/js0.. と robots.yaml のシリアルを使用)
make stop KING                   # kingspider だけ停止 (SHIN / KING SHIN も可。再開は down -> up)
make bag-record NAME=run1        # パッド操作を記録 (Ctrl+C で終了。bags/run1.bag)
make bag-play BAG=run1.bag       # 1 回再生 (記録時と同じ KING / SHIN で起動しておく)
make bag-play LOOP BAG=run1.bag  # 繰り返し再生 (Ctrl+C で終了。ニュートラルへ戻る)
make bag-list                    # 記録一覧
make down                        # 全停止
make logs / make shell
```

## Windows (PowerShell)
```powershell
.\run.ps1 setup                  # 初回: uv + .venv (グローバル Python は汚しません)
.\run.ps1 build                  # 初回のみ
.\run.ps1 attach                 # (管理者) シリアル一覧
.\run.ps1 attach -BusId 2-1,2-2  # 実機: シリアルを WSL2 へ
.\run.ps1 serial-list            # attach 後: 接続中のシリアルを一覧
.\run.ps1 serial-set             # 一覧から選んで robots.yaml を書き換え (-Robot king1 で 1 台だけ)
.\run.ps1 up -King 1 -Shin 2 -Real  # 台数を指定して実機 (-Real なしは dry_run)
.\run.ps1 bridge -Pads 2         # 別ウィンドウ: パッド -> コンテナ (UDP 5001-5003)
.\run.ps1 stop king              # kingspider だけ停止 (shin / king shin も可)
.\run.ps1 bag-record -Name run1  # 操作を記録 (bags\run1.bag)
.\run.ps1 bag-play -Bag run1.bag loop   # 再生 (loop を外すと 1 回)
.\run.ps1 down
```
