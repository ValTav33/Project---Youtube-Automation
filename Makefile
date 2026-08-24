.PHONY: test schema check-schema typecheck gallery secret-scan

test:
	python3 -m pytest -q

schema:
	python3 scripts/export_v3_schema.py

check-schema:
	python3 scripts/export_v3_schema.py --check

typecheck:
	cd remotion && npm run typecheck

gallery:
	cd remotion && npm run render:gallery

test-contracts:
	python3 -m pytest -q

secret-scan:
	! grep -nrE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=dist --exclude=package-lock.json --exclude=.env.example --exclude=.env '(sk-[A-Za-z0-9]|[0-9]{8,}:[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,})' .
