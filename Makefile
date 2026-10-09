.PHONY: setup test test-ui demo evals samples export-demo dev-api dev-ui build-ui lint-infra check deploy
setup:        ## install backend deps (dev) and frontend deps
	pip install -r backend/requirements-dev.txt && cd frontend && npm install
test:         ## backend unit and API tests (no AWS needed)
	cd backend && python -m pytest -q
test-ui:      ## frontend tests
	cd frontend && npm test
demo:         ## run the whole product loop in the terminal, no AWS, no LLM
	python scripts/demo_offline.py --day 50 --reply
evals:        ## accuracy scoreboard (offline). Live Reader too: python scripts/run_evals.py --mode live
	python scripts/run_evals.py
samples:      ## regenerate the specimen PDFs (12 bills, 3 quotations incl. the injection trap)
	python scripts/generate_samples.py
export-demo:  ## refresh the frontend's bundled static-demo data from the pipeline
	python scripts/export_demo_json.py
dev-api:      ## local API on :8787 (reads .env)
	python scripts/dev_server.py
dev-ui:       ## UI on :5173. Static demo by default; VITE_API_URL=http://localhost:8787 for the full app
	cd frontend && npm run dev
build-ui:
	cd frontend && npm run build
lint-infra:
	cfn-lint infra/template.yaml
check: test test-ui evals lint-infra build-ui   ## everything CI runs
deploy:       ## requires AWS credentials
	cd infra && sam build && sam deploy --guided
