# legacy-revive-lab — from an untested legacy service to tests, docs, coverage and CI
SHELL := /bin/bash
IMAGE := maven:3.9-eclipse-temurin-8
MVN := docker run --rm --user $$(id -u):$$(id -g) -e HOME=/tmp -e MAVEN_OPTS="-Dmaven.repo.local=/tmp/m2" \
       -v "$(PWD):/w" -v "$$HOME/.m2:/tmp/m2" -w /w/legacy-app $(IMAGE) mvn -B -Dmaven.repo.local=/tmp/m2

.PHONY: kit-test help modules system changed changed-git maps record tests verify docs coverage spans smoke advise-prompt advise-dry advise-fixture advise advise-check all clean

help:
	@echo "make modules                            which Spring services are in a repository (default: this one)"
	@echo "make modules ROOT=/path/to/repo         same, on any repository, unmodified"
	@echo "make system ROOT=/path                one diagram for the whole repository (services + call edges)"
	@echo "make changed FILES=\"a.java b.java\"   what is affected by these files -> out/CHANGED-IMPACT.md"
	@echo "make changed-git                        same, from git diff HEAD (what a PR would touch)"
	@echo "make maps       inventory, endpoint->table, error catalogue, service map (no build needed)"
	@echo "make record     replay samples/access.log against the app -> samples/golden/ (phase A)"
	@echo "make tests      generate the JUnit suite from the recordings (phase B)"
	@echo "make verify     run the suite + JaCoCo; fails under 80% (phase C)"
	@echo "make coverage   coverage report + ratchet check (make coverage UPDATE=1 to raise the baseline)"
	@echo "make spans      docs/SPANS.md from the traces the tests wrote; --check proves the maps match"
	@echo "make smoke      build the jar in a container, run it, curl it, stop it"
	@echo "make docs       regenerate docs/API.md and docs/FINDINGS.md from the recordings"
	@echo "make advise-prompt  deterministic review of the prompt contract (9 checks); no request, no key"
	@echo "make advise-dry     print the AI prompt + token estimate; no request, no key"
	@echo "make advise-fixture replay a saved answer through validate+render; no request, no key"
	@echo "make advise         one real OpenAI call (needs OPENAI_API_KEY) -> docs/ADVICE.md"
	@echo "make all            maps + tests + verify + coverage + docs"

modules:
	@python3 kit/discover.py $(if $(ROOT),--root $(ROOT),)

system:
	@python3 kit/systemmap.py $(if $(ROOT),--root $(ROOT),)

changed:
	@python3 kit/changed.py $(FILES)

changed-git:
	@python3 kit/changed.py --git

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

spans:
	@python3 kit/spanmap.py

smoke:
	@bash kit/smoke_docker.sh

kit-test:
	python3 kit/tests/test_coverage_gate.py

coverage:
	@python3 kit/coverage_gate.py $(if $(UPDATE),--update,)

advise-prompt:
	@python3 kit/advise.py --check-prompt

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
