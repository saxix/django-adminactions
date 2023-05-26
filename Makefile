VERSION=2.0.0
BUILDDIR=${PWD}/~build
BINDIR=${PWD}/~build/bin
PYTHONPATH:=${PWD}/tests/:${PWD}
DJANGO?='3.1.x'


define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z0-9_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("\033[93m%-10s\033[0m %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.mkbuilddir:
	mkdir -p ${BUILDDIR}

develop:
	CRYPTOGRAPHY_DONT_BUILD_RUST=1 pip install -e .[dev,docs]


demo:
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src django-admin.py migrate --settings=demo.settings --noinput
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src  django-admin.py loaddata adminactions.json demoproject.json --settings=demo.settings
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src  django-admin.py runserver --settings=demo.settings

lint:
	@flake8 src/ tests/
	@isort -c src/


clean:
	rm -fr ${BUILDDIR} dist *.egg-info .coverage coverage.xml pytest.xml .cache MANIFEST
	find . -name __pycache__ | xargs rm -rf
	find . -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf
	find adminactions/locale -name django.mo | xargs rm -f


fullclean:
	rm -fr .tox .cache
	rm -fr *.sqlite
	$(MAKE) clean
	mysql -e 'DROP DATABASE IF EXISTS adminactions;';
	psql -c 'DROP DATABASE IF EXISTS adminactions;' -U postgres;
	mysql -e 'DROP DATABASE IF EXISTS test_adminactions;';
	psql -c 'DROP DATABASE IF EXISTS test_adminactions;' -U postgres;

coverage:
	 py.test src tests -vv --capture=no --doctest-modules --cov=adminactions --cov-report=html --cov-config=tests/.coveragerc

docs: .mkbuilddir
	mkdir -p ${BUILDDIR}/docs
	sphinx-build -aE docs/source ${BUILDDIR}/docs
ifdef BROWSE
	open ${BUILDDIR}/docs/index.html
endif
