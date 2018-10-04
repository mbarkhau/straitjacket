.PHONY: help clean update lint test devtest install install_git_hooks default

# Helpful Links

# http://clarkgrubb.com/makefile-style-guide
# https://explainshell.com
# https://stackoverflow.com/questions/448910
# https://shiroyasha.svbtle.com/escape-sequences-a-quick-guide-1

MAKEFLAGS += --warn-undefined-variables
SHELL := /bin/bash
.SHELLFLAGS := -O extglob -e -o pipefail -c
.DEFAULT_GOAL := help
.SUFFIXES:

-include makefile.config.make

ifndef MODULE_SRC_PATH
	MODULE_SRC_PATH := $(notdir $(abspath .))
endif

MODULE_SRC_PATH = src/$(PACKAGE_NAME)/

PLATFORM = $(shell uname -s)

# miniconda is shared between projects
CONDA_ROOT := $(HOME)/miniconda3
CONDA := $(CONDA_ROOT)/bin/conda

PYENV37 := $(CONDA_ROOT)/envs/$(PACKAGE_NAME)_py37
PYENV36 := $(CONDA_ROOT)/envs/$(PACKAGE_NAME)_py36
PYTHON37 := $(PYENV37)/bin/python
PYTHON36 := $(PYENV36)/bin/python

# default version for development
PYENV = $(PYENV36)
PYTHON = $(PYTHON36)


build/envs.txt: requirements/conda.txt
	@mkdir -p build/

	@if [[ ! -f $(CONDA) ]] && [[ $(PLATFORM) == "Linux" ]]; then \
		echo "installing miniconda ..."; \
		wget "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh" \
			-O build/miniconda3.sh; \
	fi
	@if [[ ! -f $(CONDA) ]] && [[ $(PLATFORM) == "Darwin" ]]; then \
		wget "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh" \
			-O build/miniconda3.sh; \
	fi

	@if [[ ! -f $(CONDA) ]]; then \
		bash build/miniconda3.sh -b -p $(CONDA_ROOT); \
		rm build/miniconda3.sh; \
	fi

	@if [[ ! -f $(PYTHON37) ]]; then \
		echo "creating env $(PACKAGE_NAME)_py37 ..."; \
		$(CONDA) create --name $(PACKAGE_NAME)_py37 python=3.7 --yes; \
	fi

	@if [[ ! -f $(PYTHON36) ]]; then \
		echo "creating env $(PACKAGE_NAME)_py36 ..."; \
		$(CONDA) create --name $(PACKAGE_NAME)_py36 python=3.6 --yes; \
	fi

	$(CONDA) install --name $(PACKAGE_NAME)_py37 \
		--channel conda-forge --yes \
		$$(grep -o '^[^#][^ ]*' requirements/conda.txt)

	$(CONDA) install --name $(PACKAGE_NAME)_py36 \
		--channel conda-forge --yes \
		$$(grep -o '^[^#][^ ]*' requirements/conda.txt)

	$(CONDA) env list \
		| grep $(PACKAGE_NAME) \
		| rev | cut -d " " -f1 \
		| rev | sort > build/envs.txt.tmp

	$(PYTHON36) --version >> build/envs.txt.tmp 2>>build/envs.txt.tmp
	$(PYTHON37) --version >> build/envs.txt.tmp 2>>build/envs.txt.tmp

	mv build/envs.txt.tmp build/envs.txt



build/deps.txt: build/envs.txt requirements/*.txt
	@mkdir -p build/

	$(PYTHON37) -m pip install --upgrade pip
	$(PYTHON36) -m pip install --upgrade pip

	$(PYTHON37) -m pip install \
		--upgrade --disable-pip-version-check \
		$$(grep -o '^[^#][^ ]*' requirements/pypi.txt)

	$(PYTHON36) -m pip install \
		--upgrade --disable-pip-version-check \
		$$(grep -o '^[^#][^ ]*' requirements/pypi.txt)

	# NOTE (mb 2018-09-21): vendored dependencies are installed
	# 	both in the virtual environment as well as in the
	# 	vendor/ directory. This is to prevent transitive
	#	dependencies from being installed in vendor/
	$(PYTHON36) -m pip install \
		--upgrade --disable-pip-version-check \
		$$(grep -o '^[^#][^ ]*' requirements/integration.txt) \
		$$(grep -o '^[^#][^ ]*' requirements/vendor.txt) \
		$$(grep -o '^[^#][^ ]*' requirements/development.txt);

	$(PYTHON36) -m pip install \
		--upgrade --disable-pip-version-check \
		--no-binary --no-deps --target vendor/ \
		$$(grep -o '^[^#][^ ]*' requirements/vendor.txt);

	@rm -f build/deps.txt.tmp
	@printf "\npip freeze for $(PYENV36):\n" >> build/deps.txt.tmp
	$(PYTHON37) -m pip freeze >> build/deps.txt.tmp
	@printf "\n" >> build/deps.txt.tmp

	@printf "\npip freeze for $(PYENV37):\n" >> build/deps.txt.tmp
	$(PYTHON36) -m pip freeze >> build/deps.txt.tmp
	@printf "\n" >> build/deps.txt.tmp
	@mv build/deps.txt.tmp build/deps.txt


## This help message
help:
	@printf "Available make targets for \033[97m$(PACKAGE_NAME)\033[0m:\n\n"
	@grep -hzoP '\n\n##.*?\n([a-zA-Z_-]+(?=:)|(?=\n\n))' $(MAKEFILE_LIST) \
		| grep -zoP '[^#]+' \
		| awk 'BEGIN { FS = "\n"; RS = ""; }; { printf "    \033[36m%-9s\033[0m %s\n", $$2, $$1}'
	@printf "\n"

	@if [[ ! -f $(PYTHON) ]]; then \
	echo "Missing python interpreter at $(PYTHON) !"; \
	echo "You problably want to install first:"; \
	echo ""; \
	echo "    make install"; \
	echo ""; \
	exit 0; \
	fi

	@if [[ ! -f $(CONDA) ]]; then \
	echo "No conda installation found!"; \
	echo "You problably want to install first:"; \
	echo ""; \
	echo "    make install"; \
	echo ""; \
	exit 0; \
	fi

	echo



## -- Project Setup --


## Delete conda envs and cache 💩
clean:
	@if test -f $(PYTHON37); then \
	$(CONDA) env remove --name $(PACKAGE_NAME)_py37 --yes; \
	fi

	@if test -f $(PYTHON36); then \
	$(CONDA) env remove --name $(PACKAGE_NAME)_py36 --yes; \
	fi

	rm -f build/envs.txt
	rm -f build/deps.txt
	rm -rf vendor/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf vendor/__pycache__/
	@printf "\n setup/update completed  ✨ 🍰 ✨ \n\n"


## Setup python virtual environments
install: build/deps.txt


## Update dependencies (pip install -U ...)
update: build/deps.txt


## TODO: Install git pre-commit and pre-push hooks
git_hooks:
	# TODO pre commit should pass at `make fmt lint`
	# TODO pre push should pass `make test`
	echo "Not Implemented"


## -- Development --


## Run code formatter on src/ and test/
fmt:
	@$(PYENV)/bin/sjfmt --py36 --skip-string-normalization --line-length=100 \
		 $(MODULE_SRC_PATH)/*.py test/*.py


# TODO: add linting for .md files using readme_renderer

## Run flake8 linter and mypy type checker
lint:
	@printf "flake8 .....\e[s\n"
	@$(PYENV)/bin/flake8 $(MODULE_SRC_PATH)
	@printf "\e[u\e[1A ok\n"

	@printf "mypy .......\e[s\n"
	@MYPYPATH=stubs/:vendor/ $(PYTHON) -m mypy $(MODULE_SRC_PATH)
	@printf "\e[u\e[1A ok\n"

	@printf "docs .......\e[s\n"
	@printf "\e[u\e[1A NA \n"


## Run pytest unit and integration tests
test:
	ENV=dev PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(PYTHON) -m pytest -v \
		--doctest-modules \
		--cov-report html \
		--cov-report term \
		--cov=$(PACKAGE_NAME) \
		test/ src/


## -- Helpers --


## Drop into an ipython shell with correct env variables set
ipy:
	@PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(PYENV)/bin/ipython


## like `make test`, but with debug parameters
devtest:
	ENV=dev PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		$(PYTHON) -m pytest -v \
		--doctest-modules \
		--cov-report term \
		--cov=$(PACKAGE_NAME) \
		--verbose \
		--capture=no \
		--exitfirst \
		test/ src/


include makefile.extra.make
