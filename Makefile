# spider-docker (Ubuntu)。 例: make up KING=1 SHIN=2 / 実機: make up DRY_RUN=0 KING=1
-include .env
export
DRY_RUN    ?= 1
JOY_SOURCE ?= js
COMPOSE_BASE := docker compose -f docker/docker-compose.yml
GEN := docker run --rm -e DRY_RUN=$(DRY_RUN) -e JOY_SOURCE=$(JOY_SOURCE) -e KING=$(KING) -e SHIN=$(SHIN) \
       -v $(CURDIR)/robots.yaml:/config/robots.yaml:ro --entrypoint python3 \
       spider-docker:latest /opt/spider/spider_gen.py compose /config/robots.yaml

.PHONY: build up down stop serial-list serial-set bag-record bag-play bag-list logs shell devices help KING SHIN LOOP

build:   ## イメージをビルド
	$(COMPOSE_BASE) build

devices: ## robots.yaml から devices 設定を生成
	@$(GEN) > docker/compose.devices.yml

up: devices ## 起動 (KING=台数 SHIN=台数 / 実機は DRY_RUN=0)
	$(COMPOSE_BASE) -f docker/compose.devices.yml up -d
	@echo "logs: make logs / stop: make down"

down:    ## 停止
	$(COMPOSE_BASE) down

stop:    ## 種別ごとに停止 (make stop KING / SHIN / KING SHIN)。再開は down -> up
	docker exec -e STOP_KING=$(if $(filter KING,$(MAKECMDGOALS)),1) -e STOP_SHIN=$(if $(filter SHIN,$(MAKECMDGOALS)),1) spider /opt/spider/entrypoint.sh stop

serial-list: ## 接続中のシリアルデバイスを一覧
	python3 tools/serial_tool.py list

serial-set: ## 一覧から選んで robots.yaml の serial を書き換え (ROBOT=king1 でその 1 台だけ)
	python3 tools/serial_tool.py set $(if $(ROBOT),--robot $(ROBOT))

bag-record: ## 操作を記録 (NAME=名前 省略で日時)。Ctrl+C で終了 -> bags/
	docker exec -it -e BAG_NAME=$(NAME) spider /opt/spider/entrypoint.sh bag-record

bag-play: ## 再生 (BAG=ファイル名 [LOOP で繰り返し]) 例: make bag-play LOOP BAG=run1.bag
	docker exec -it -e BAG=$(BAG) -e LOOP=$(if $(filter LOOP,$(MAKECMDGOALS)),1) spider /opt/spider/entrypoint.sh bag-play

bag-list: ## 記録済みの bag 一覧
	@ls -lh bags/*.bag 2>/dev/null || echo "(bag がありません)"

# make stop KING / make bag-play LOOP のための空ターゲット (語を引数として受けるだけ)
KING SHIN LOOP: ; @:

logs:    ## ログを表示
	$(COMPOSE_BASE) logs -f

shell:   ## 実行中コンテナに入る
	docker exec -it spider bash -c 'source /opt/ros/noetic/setup.bash && source /spider_ws/devel/setup.bash && exec bash'

help:    ## ヘルプ
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-10s %s\n", $$1, $$2}'
