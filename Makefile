# Canonical command interface (CLAUDE.md §11), wired for this repository: standard-library
# Python under src/ and tests/, formatted and linted by ruff through uv (pyproject.toml).
# Every agent, hook, and CI job calls ONLY these targets. Optional FILE=<path> narrows
# format/lint to one file. Inherited foundation scripts under scripts/ are tested by their
# own suite and byte-compiled here; they are not reformatted (the inheritance contract
# requires them to stay byte-identical to the parent).

.PHONY: setup format lint test test-unit test-integration coverage build run \
        security-scan sbom clean help doctor fleet-audit

FILE ?=
FLEET_WORKSPACE_ROOT ?= ..

help: ## List available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

setup: ## Install toolchain (uv-managed dev group) and git hooks — idempotent
	uv sync
	@if command -v pre-commit >/dev/null 2>&1; then pre-commit install --hook-type pre-commit --hook-type pre-push; else echo "[project] setup: pre-commit not installed — local hooks skipped (CI runs the same gates)"; fi

format: ## Auto-format src/ and tests/ (all, or FILE=<path>)
ifneq ($(FILE),)
	@case "$(FILE)" in *.py) uv run ruff format "$(FILE)" && uv run ruff check --fix-only "$(FILE)" ;; *) : ;; esac
else
	uv run ruff format src tests
	uv run ruff check --fix-only src tests
endif

lint: ## Check-only, zero warnings (COD-001): ruff format check + ruff check; byte-compile scripts/
ifneq ($(FILE),)
	@case "$(FILE)" in *.py) uv run ruff format --check "$(FILE)" && uv run ruff check "$(FILE)" ;; *) : ;; esac
else
	uv run ruff format --check src tests
	uv run ruff check src tests
	@python3 -m compileall -q scripts
endif

test: test-unit test-integration ## Full test suite (unit + integration) — TST-001
	@bash .claude/hooks/tests/guard-bash.test.sh

test-unit: ## Fast unit suite: inherited foundation tests + tests/**/unit (no I/O) — TST-001
	@python3 -m unittest discover -s scripts/tests -p 'test_*.py'
	@python3 -m unittest discover -s tests -t . -p 'test_*.py' -k '.unit.'

test-integration: ## Integration suite: tests/**/integration (real files in temp dirs) — TST-001
	@python3 -m unittest discover -s tests -t . -p 'test_*.py' -k '.integration.'

coverage: ## Test with coverage report — TST-003 ratchet
	@rm -rf coverage
	@python3 -m trace --count --missing --summary \
		--ignore-dir '/usr:/opt:/Library' --coverdir coverage \
		--module unittest discover -s scripts/tests -p 'test_*.py'
	@python3 -m trace --count --missing --summary \
		--ignore-dir '/usr:/opt:/Library' --coverdir coverage \
		--module unittest discover -s tests -t . -p 'test_*.py'
	@bash .claude/hooks/tests/guard-bash.test.sh

build: ## Produce deployable artifact
	@echo "[project] build: not applicable — no deployable artifact; scripts run from the checkout"

run: ## Run the application locally
	@echo "[project] run: not applicable — invoke a module directly, e.g. uv run python -m src.modules.<name>.interface.cli --help"

security-scan: ## Local security sweep (secrets + deps + config)
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner; else echo "[project] gitleaks not installed — CI still enforces SEC-002"; fi
	@if command -v trivy >/dev/null 2>&1; then trivy fs --scanners vuln,misconfig,secret --exit-code 1 .; else echo "[project] trivy not installed — CI still enforces SEC-030"; fi

sbom: ## Generate SBOM (SPDX + CycloneDX) into ./dist — REL-020
	@mkdir -p dist
	@if command -v syft >/dev/null 2>&1; then syft . -o spdx-json=dist/sbom.spdx.json -o cyclonedx-json=dist/sbom.cdx.json && echo "SBOM written to dist/"; else echo "[project] syft not installed — release workflow generates the authoritative SBOM"; fi

clean: ## Remove build artifacts and caches (workspace only — GR-031)
	@rm -rf dist coverage .ruff_cache
	@find . -type d -name "__pycache__" -not -path "./.git/*" -not -path "./.venv/*" -exec rm -rf {} +

doctor: ## Foundation self-check: metadata invariants + guard-hook tests (stack-independent)
	@bash scripts/template-check.sh
	@bash .claude/hooks/tests/guard-bash.test.sh

fleet-audit: ## Audit every configured local inheritance relationship without writes
	@python3 scripts/template_inheritance.py fleet-audit \
		--config docs/foundation/inheritance-fleet.json \
		--workspace-root "$(FLEET_WORKSPACE_ROOT)"

# ---------------------------------------------------------------------------
# Project extensions (below the canonical contract; profiles/README.md)
# ---------------------------------------------------------------------------

VAULT ?=

rules-validate: ## Validate the vault's writing rules (30_memory/feedback/ja-*.md); VAULT=<path> overrides $$OBSIDIAN_VAULT_PATH
	@python3 -m src.modules.rules.interface.cli $(if $(VAULT),--vault "$(VAULT)",)
