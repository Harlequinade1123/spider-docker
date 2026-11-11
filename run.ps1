# spider-docker (Windows / PowerShell)
# 使い方: .\run.ps1 <setup|attach|bridge|up|down|logs|shell|build> [options]
param(
  [Parameter(Position = 0)][string]$Cmd = "help",
  [string[]]$BusId = @(),      # attach: usbipd の BUSID (例 -BusId 2-1,2-2)
  [int]$Pads = 1,              # bridge: パッド数 (1-3)
  [int]$King = 0,              # up: kingspider の台数
  [int]$Shin = 0,              # up: shin_spider の台数 (両方 0 なら robots.yaml の全台)
  [string]$Name = "",          # bag-record: ファイル名 (省略で日時)
  [string]$Bag = "",           # bag-play: bags/ 内のファイル名
  [string]$Robot = "",         # serial-set: 対象ロボット名 (例 king1。省略で全部)
  [Parameter(ValueFromRemainingArguments = $true)][string[]]$Targets = @(),  # stop: king / shin、bag-play: loop
  [switch]$Real                # up: 実機 (DRY_RUN=0)
)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Compose = @("compose", "-f", "$Root\docker\docker-compose.yml")
$Dry = if ($Real) { "0" } else { "1" }
$env:DRY_RUN = $Dry
$env:JOY_SOURCE = "udp"
$KingS = if ($King -gt 0) { "$King" } else { "" }
$ShinS = if ($Shin -gt 0) { "$Shin" } else { "" }
$env:KING = $KingS
$env:SHIN = $ShinS

switch ($Cmd) {
  "setup" {   # uv と venv (.venv) を用意。グローバル Python は使わない
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { winget install --id astral-sh.uv -e }
    uv venv "$Root\.venv"
    uv pip install --python "$Root\.venv\Scripts\python.exe" -r "$Root\tools\requirements.txt"
  }
  "attach" {  # シリアルを WSL2 に渡す (管理者 PowerShell。BusId 省略で一覧表示)
    if ($BusId.Count -eq 0) { usbipd list; break }
    foreach ($b in $BusId) { usbipd bind --busid $b; usbipd attach --wsl --busid $b }
  }
  "bridge" {  # パッド -> UDP (別ウィンドウで実行)
    & "$Root\.venv\Scripts\python.exe" "$Root\tools\win_joy_bridge.py" --pads $Pads
  }
  "build" { docker @Compose build }
  "up" {
    $gen = docker run --rm -e DRY_RUN=$Dry -e JOY_SOURCE=udp -e KING=$KingS -e SHIN=$ShinS -v "${Root}\robots.yaml:/config/robots.yaml:ro" `
      --entrypoint python3 spider-docker:latest /opt/spider/spider_gen.py compose /config/robots.yaml
    # BOM なし UTF-8 / LF で書く (PowerShell 5.1 の Set-Content -Encoding utf8 は BOM 付きになるため)
    [System.IO.File]::WriteAllText("$Root\docker\compose.devices.yml", (($gen -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
    docker @Compose -f "$Root\docker\compose.devices.yml" up -d
  }
  "stop"  {   # .\run.ps1 stop king / shin / king shin
    $sk = if ($Targets -contains "king") { "1" } else { "" }
    $ss = if ($Targets -contains "shin") { "1" } else { "" }
    docker exec -e "STOP_KING=$sk" -e "STOP_SHIN=$ss" spider /opt/spider/entrypoint.sh stop
  }
  # シリアルは WSL2 側に見える (attach 後)。WSL の python3 で一覧/書き換えする
  "serial-list" { wsl --cd $Root python3 tools/serial_tool.py list }
  "serial-set"  {   # .\run.ps1 serial-set [-Robot king1]
    if ($Robot) { wsl --cd $Root python3 tools/serial_tool.py set --robot $Robot }
    else        { wsl --cd $Root python3 tools/serial_tool.py set }
  }
  "bag-record" {   # .\run.ps1 bag-record [-Name run1]
    docker exec -it -e "BAG_NAME=$Name" spider /opt/spider/entrypoint.sh bag-record
  }
  "bag-play" {     # .\run.ps1 bag-play -Bag run1.bag [loop]
    $lp = if ($Targets -contains "loop") { "1" } else { "" }
    docker exec -it -e "BAG=$Bag" -e "LOOP=$lp" spider /opt/spider/entrypoint.sh bag-play
  }
  "bag-list" { Get-ChildItem "$Root\bags\*.bag" -ErrorAction SilentlyContinue }
  "down"  { docker @Compose down }
  "logs"  { docker @Compose logs -f }
  "shell" { docker exec -it spider bash -c "source /opt/ros/noetic/setup.bash && source /spider_ws/devel/setup.bash && exec bash" }
  default {
    "setup | attach [-BusId ..] | bridge [-Pads N] | build | up [-King N] [-Shin N] [-Real] | stop [king] [shin] | serial-list | serial-set [-Robot N] | bag-record [-Name N] | bag-play -Bag F [loop] | bag-list | down | logs | shell"
  }
}
