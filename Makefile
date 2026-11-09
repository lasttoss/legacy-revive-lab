# legacy-revive-lab — from an untested legacy service to tests, docs, coverage and CI
SHELL := /bin/bash
IMAGE := maven:3.9-eclipse-temurin-8
MVN := docker run --rm --user $$(id -u):$$(id -g) -e HOME=/tmp -e MAVEN_OPTS="-Dmaven.repo.local=/tmp/m2" \
       -v "$(PWD):/w" -v "$$HOME/.m2:/tmp/m2" -w /w/legacy-app $(IMAGE) mvn -B -Dmaven.repo.local=/tmp/m2

.PHONY: help maps record tests verify docs coverage advise-dry advise-fixture advise advise-check all clean

help:
	@echo "make maps       inventory, endpoint->table, error catalogue, service map (no build needed)"
	@echo "make record     replay samples/access.log against the app -> samples/golden/ (phase A)"
	@echo "make tests      generate the JUnit suite from the recordings (phase B)"
	@echo "make verify     run the suite + JaCoCo; fails under 80% (phase C)"
	@echo "make coverage   coverage report + ratchet check (make coverage UPDATE=1 to raise the baseline)"
	@echo "make docs       regenerate docs/API.md and docs/FINDINGS.md from the recordings"
	@echo "make advise-dry     print the AI prompt + token estimate; no request, no key"
	@echo "make advise-fixture replay a saved answer through validate+render; no request, no key"
	@echo "make advise         one real OpenAI call (needs OPENAI_API_KEY) -> docs/ADVICE.md"
	@echo "make all            maps + tests + verify + coverage + docs"

maps:
	@python3 kit/inventory.py
	@python3 kit/sqlmap.py
	@python3 kit/errors.py
	@python3 kit/servicemap.py

record:
	$(MVN) -q -Dtest=Recorder test

tests:
	@python3 kit/gen_tests.py

verify:
	$(MVN) verify

docs:
	@python3 kit/gen_docs.py

coverage:
	@python3 kit/coverage_gate.py $(if $(UPDATE),--update,)

advise-dry:
	@python3 kit/advise.py --dry-run

advise-fixture:
	@python3 kit/advise.py --fixture

advise:
	@python3 kit/advise.py

advise-check:
	@python3 kit/advise.py --check

all: maps tests verify coverage docs

clean:
	rm -rf legacy-app/target
