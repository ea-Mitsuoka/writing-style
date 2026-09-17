# Canonical command interface (CLAUDE.md §11), wired for this repository: standard-library
# Python scripts that process Markdown rule files. Every agent, hook, and CI job calls ONLY
# these targets. Optional FILE=<path> narrows format/lint to one file.
#
# No formatter or type checker is configured yet: the repository holds no project code
# beyond the inherited foundation scripts. When the first project script lands, wire
# `format` and `lint` from profiles/python-uv/Makefile in the same PR (GR-023 applies to
# the added tooling).

.PHONY: setup format lint test test-unit test-integration coverage build run \
        security-scan sbom clean help doctor fleet-audit

FILE ?=
FLEET_WORKSPACE_ROOT ?= ..

help: ## List available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

setup: ## Install git hooks (idempotent); no package dependencies yet
	@if command -v pre-commit >/dev/null 2>&1; then pre-commit install --hook-type pre-commit --hook-type pre-push; else echo "[project] setup: pre-commit not installed — local hooks skipped (CI runs the same gates)"; fi

format: ## Auto-format (all, or FILE=<path>)
	@echo "[project] format: not applicable — no formatter configured; wire ruff from profiles/python-uv when the first project script lands"

lint: ## Check-only, zero warnings (COD-001): byte-compile every Python file (all, or FILE=<path>)
ifneq ($(FILE),)
	@case "$(FILE)" in *.py) python3 -m py_compile "$(FILE)" ;; *) : ;; esac
else
	@python3 -m compileall -q scripts
endif

test: test-unit test-integration ## Full test suite (unit + integration) — TST-001
	@bash .claude/hooks/tests/guard-bash.test.sh

test-unit: ## Fast unit suite only, used by pre-commit — TST-001
	@python3 -m unittest discover -s scripts/tests -p 'test_*.py'

test-integration: ## Integration suite (may use containers)
	@echo "[project] test-integration: not applicable — no external integration surface"

coverage: ## Test with coverage report — TST-003 ratchet
	@rm -rf coverage
	@python3 -m trace --count --missing --summary \
		--ignore-dir '/usr:/opt:/Library' --coverdir coverage \
		--module unittest discover -s scripts/tests -p 'test_*.py'
	@bash .claude/hooks/tests/guard-bash.test.sh

build: ## Produce deployable artifact
	@echo "[project] build: not applicable — no deployable artifact; scripts run from the checkout"

run: ## Run the application locally
	@echo "[project] run: not applicable — invoke a script directly, e.g. python3 scripts/<name>.py --help"

security-scan: ## Local security sweep (secrets + deps + config)
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner; else echo "[project] gitleaks not installed — CI still enforces SEC-002"; fi
	@if command -v trivy >/dev/null 2>&1; then trivy fs --scanners vuln,misconfig,secret --exit-code 1 .; else echo "[project] trivy not installed — CI still enforces SEC-030"; fi

sbom: ## Generate SBOM (SPDX + CycloneDX) into ./dist — REL-020
	@mkdir -p dist
	@if command -v syft >/dev/null 2>&1; then syft . -o spdx-json=dist/sbom.spdx.json -o cyclonedx-json=dist/sbom.cdx.json && echo "SBOM written to dist/"; else echo "[project] syft not installed — release workflow generates the authoritative SBOM"; fi

clean: ## Remove build artifacts and caches (workspace only — GR-031)
	@rm -rf dist coverage
	@find . -type d -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +

doctor: ## Foundation self-check: metadata invariants + guard-hook tests (stack-independent)
	@bash scripts/template-check.sh
	@bash .claude/hooks/tests/guard-bash.test.sh

fleet-audit: ## Audit every configured local inheritance relationship without writes
	@python3 scripts/template_inheritance.py fleet-audit \
		--config docs/foundation/inheritance-fleet.json \
		--workspace-root "$(FLEET_WORKSPACE_ROOT)"
