#
# Makefile for fly_in by andmarti
#

GREEN = \033[1;92m
YELLOW = \033[1;93m
RESET = \033[0m
NAME = fly_in
FLAKEFLAGS = --exclude venv
MYPYFLAGS= --exclude venv \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

venv:
	@echo "$(YELLOW)venv loading...$(RESET)"
	@test -d venv || python3 -m venv venv
	@echo "$(GREEN)venv created.$(RESET)"

install:
	pip install --upgrade pip && \
	pip install flake8 mypy build setuptools wheel mazegen-1.0.0.tar.gz


run:
	python3 $(NAME) $(CONFIG)

debug:
	python3 -m pdb $(NAME) $(CONFIG)

clean:
	find . -type d -name "*.egg-info" -exec rm -rf {} + 
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type f -name "*.txt" ! -name "config.txt" -delete
	rm -rf build dist

lint:
	@echo "$(GREEN)==============$(RESET)"
	@echo "$(GREEN)=== flake8 ===$(RESET)"
	@echo "$(GREEN)==============$(RESET)"
	@flake8 . $(FLAKEFLAGS) || true
	@echo "$(GREEN)============$(RESET)"
	@echo "$(GREEN)=== mypy ===$(RESET)"
	@echo "$(GREEN)============$(RESET)"
	@mypy . $(MYPYFLAGS) || true

