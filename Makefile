.PHONY: up down test test-deadlock report all load load-read

-include .env

BASE_URL ?= http://localhost:8080
LOAD_USERS ?= 20
LOAD_SPAWN_RATE ?= 5
LOAD_DURATION ?= 90s

up:
	docker compose up -d
	@echo "Waiting for API..."
	@until curl -sf $(BASE_URL)/swagger/doc.json > /dev/null 2>&1; do sleep 1; done
	@echo "API is up."

down:
	docker compose down

test:
	rm -rf reports/allure-results
	pytest -m "not deadlock"

test-deadlock:
	RUN_DEADLOCK_TEST=1 pytest -m deadlock

report:
	allure serve reports/allure-results

report-static:
	allure generate reports/allure-results -o reports/allure-report --single-file --clean
	@echo "Open reports/allure-report/index.html directly in a browser (no server needed)."

# Expected to crash the service (BUG-12) -- that crash is the finding. See loadtest/locustfile.py.
load:
	mkdir -p reports/load
	locust -f loadtest/locustfile.py ApiUser --host=$(BASE_URL)/api/v1 \
		--headless -u $(LOAD_USERS) -r $(LOAD_SPAWN_RATE) -t $(LOAD_DURATION) \
		--csv=reports/load/results --html=reports/load/report.html

# Crash-free read-only baseline (avoids BUG-12's concurrent map read/write).
load-read:
	mkdir -p reports/load
	locust -f loadtest/locustfile.py ReadOnlyUser --host=$(BASE_URL)/api/v1 \
		--headless -u $(LOAD_USERS) -r $(LOAD_SPAWN_RATE) -t $(LOAD_DURATION) \
		--csv=reports/load/results-read --html=reports/load/report-read.html

all: down up test down
