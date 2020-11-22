VERSION=2.0.0
BUILDDIR=${PWD}/~build
BINDIR=${PWD}/~build/bin
PYTHONPATH:=${PWD}/tests/:${PWD}
DJANGO?='3.1.x'

.mkbuilddir:
	mkdir -p ${BUILDDIR}

develop:
	pip install -e .[dev]


demo:
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src django-admin.py migrate --settings=demo.settings --noinput
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src  django-admin.py loaddata adminactions.json demoproject.json --settings=demo.settings
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src  django-admin.py runserver --settings=demo.settings

qa:
	flake8 src/ tests/
	isort -rc src tests --check-only
	check-manifest
	py.test tests/ --cov=adminactions --cov-report=html --cov-config=tests/.coveragerc

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
