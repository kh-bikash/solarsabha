.PHONY: setup test demo evals samples export-demo dev-api dev-ui build-ui lint-infra deploy
setup:        ## install backend deps (dev) and frontend deps
	pip install -r backend/requirements-dev.txt && cd frontend && npm install
test:         ## run unit tests (no AWS needed)
	cd backend && python -m pytest -q
demo:         ## run the whole product loop in the terminal, no AWS, no LLM
	python scripts/demo_offline.py --day 50 --reply
evals:        ## accuracy scoreboard (offline). Use: python scripts/run_evals.py --mode live  for the Reader
	python scripts/run_evals.py
samples:      ## generate sample PDFs (12 bills, 3 quotes incl. the injection trap)
	python scripts/generate_samples.py
export-demo:  ## refresh the frontend's bundled demo data from the pipeline
	python scripts/export_demo_json.py
dev-api:      ## local API on :8787
	python scripts/dev_server.py
dev-ui:       ## UI on :5173 (MOCK data by default; set VITE_API_URL=http://localhost:8787 for LIVE)
	cd frontend && npm run dev
build-ui:
	cd frontend && npm run build
lint-infra:
	cfn-lint infra/template.yaml
deploy:       ## requires AWS credentials
	cd infra && sam build && sam deploy --guided
