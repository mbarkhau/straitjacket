

build/README.html: build/.install.make_marker *.rst
	@cat README.rst > build/.full_readme.rst
	@echo "\n" >> build/.full_readme.rst
	@cat CONTRIBUTING.rst >> build/.full_readme.rst
	@echo "\n" >> build/.full_readme.rst
	@cat CHANGELOG.rst >> build/.full_readme.rst
	@$(PYENV37)/bin/rst2html5 --strict \
		build/.full_readme.rst > build/README.html.tmp
	@mv build/README.html.tmp build/README.html
	@echo "updated build/README.html"


doc: build/README.html



build/.src_files.txt: setup.py build/envs.txt $(MODULE_PATH)*.py
	@mkdir -p build/
	@ls -l setup.py build/envs.txt $(MODULE_PATH)*.py > build/.src_files.txt.tmp
	@mv build/.src_files.txt.tmp build/.src_files.txt


rm_site_packages:
	# whackamole
	rm -rf $(PYENV36)/lib/python3.6/site-packages/$(PACKAGE_NAME)/
	rm -rf $(PYENV36)/lib/python3.6/site-packages/$(PACKAGE_NAME)*.dist-info/
	rm -rf $(PYENV36)/lib/python3.6/site-packages/$(PACKAGE_NAME)*.egg-info/
	rm -f $(PYENV36)/lib/python3.6/site-packages/$(PACKAGE_NAME)*.egg

	rm -rf $(PYENV37)/lib/python3.6/site-packages/$(PACKAGE_NAME)/
	rm -rf $(PYENV37)/lib/python3.6/site-packages/$(PACKAGE_NAME)*.dist-info/
	rm -rf $(PYENV37)/lib/python3.6/site-packages/$(PACKAGE_NAME)*.egg-info/
	rm -f $(PYENV37)/lib/python3.6/site-packages/$(PACKAGE_NAME)*.egg


build/.local_install.make_marker: build/.src_files.txt rm_site_packages
	@echo "installing $(PACKAGE_NAME).."
	@$(PYTHON37) setup.py install --no-compile --verbose
	@mkdir -p build/
	@$(PYTHON37) -c "import $(PACKAGE_NAME)"
	@echo "install completed for $(PACKAGE_NAME)"
	@touch build/.local_install.make_marker


# build
.PHONY: build
build: build/.local_install.make_marker
	@mkdir -p $(BUILD_LOG_DIR)
	@echo "writing full build log to $(BUILD_LOG_FILE)"
	@echo "building $(PACKAGE_NAME).."
	@$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3 >> $(BUILD_LOG_FILE)
	@echo "build completed for $(PACKAGE_NAME)"

# upload
.PHONY: upload
upload: build/.install.make_marker build/README.html
	$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3
	$(PYENV37)/bin/twine upload $(BDIST_WHEEL_FILE)

# run: build/.install.make_marker

# run
.PHONY: run
run:
	# PYTHONPATH=src/:$$PYTHONPATH $(PYTHON37) -m straitjacket.sjfmt src/straitjacket/sjfmt.py
	# PYTHONPATH=src/:$$PYTHONPATH $(PYTHON37) -m straitjacket.sjfmt setup.py
	PYTHONPATH=src/:$$PYTHONPATH $(PYTHON37) -m straitjacket setup.py

