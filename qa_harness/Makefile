# CarbonTally QA Harness v1 — Make targets.
#
# BUILD / SELF-TEST ONLY. None of these targets contact the CarbonTally
# application; they operate on the Harness itself.

PYTHON ?= python3

.PHONY: help install selftest test preflight-check clean

help:
	@echo "CarbonTally QA Harness v1"
	@echo "  make install          install core + test dependencies"
	@echo "  make selftest         run Harness self-tests (pytest, no app contact)"
	@echo "  make preflight-check  validate config + identity generation (static only)"
	@echo "  make clean            remove __pycache__ and empty runtime dirs content"

install:
	$(PYTHON) -m pip install -r requirements.txt

selftest: install
	$(PYTHON) -m pytest tests -v

preflight-check:
	$(PYTHON) -c "from qa_harness.scripts import preflight; print('preflight imports OK')"
	$(PYTHON) scripts/preflight.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find evidence findings -type f -name '.gitkeep' -prune -o -type f -print -delete 2>/dev/null || true
