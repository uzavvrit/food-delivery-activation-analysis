.PHONY: all test check clean
all:
	python -m scripts.run_all
test:
	python -m pytest -q
check: test all
clean:
	rm -rf data/raw .pytest_cache
