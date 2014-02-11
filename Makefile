VERSION=2.0.0
BUILDDIR=${PWD}/~build
BINDIR=${PWD}/~build/bin
PYTHONPATH := ${PWD}/demo/:${PWD}
DJANGO_14=django==1.4.10
DJANGO_15=django==1.5.5
DJANGO_16=django==1.6
DJANGO_DEV=git+git://github.com/django/django.git
CASPERJS_DIR=${BUILDDIR}/casperjs
PHANTOMJS_DIR=${BUILDDIR}/phantomjs

mkbuilddir:
	mkdir -p ${BUILDDIR} ${BINDIR}


install-deps:
	pip install -q \
	        -r adminactions/requirements/install.pip \
	        -r adminactions/requirements/testing.pip \
	        python-coveralls


install-casperjs: mkbuilddir
	@sh -c "if [ -d ${CASPERJS_DIR} ]; then cd ${CASPERJS_DIR} && git pull; else git clone git://github.com/n1k0/casperjs.git ${CASPERJS_DIR}; fi"


locale:
	cd adminactions && django-admin.py makemessages -l en
	export PYTHONPATH=${PYTHONPATH} && cd adminactions && django-admin.py compilemessages --settings=${DJANGO_SETTINGS_MODULE}


init-db:
	@sh -c "if [ '${DBENGINE}' = 'mysql' ]; then mysql -e 'DROP DATABASE IF EXISTS adminactions;'; fi"
	@sh -c "if [ '${DBENGINE}' = 'mysql' ]; then mysql -e 'create database IF NOT EXISTS adminactions CHARSET=utf-8 COLLATE=utf8_general_ci;'; fi"
	@sh -c "if [ '${DBENGINE}' = 'mysql' ]; then pip install MySQL-python; fi"

	@sh -c "if [ '${DBENGINE}' = 'pg' ]; then psql -c 'DROP DATABASE IF EXISTS adminactions;' -U postgres; fi"
	@sh -c "if [ '${DBENGINE}' = 'pg' ]; then psql -c 'CREATE DATABASE adminactions;' -U postgres; fi"
	@sh -c "if [ '${DBENGINE}' = 'pg' ]; then pip install -q psycopg2; fi"


test:
	py.test


coverage: mkbuilddir
	py.test --cov=adminactions --cov-report=html --cov-config=.coveragerc -vvv


ci: init-db install-deps
	@sh -c "if [ '${DJANGO}' = '1.4.x' ]; then pip install ${DJANGO_14}; fi"
	@sh -c "if [ '${DJANGO}' = '1.5.x' ]; then pip install ${DJANGO_15}; fi"
	@sh -c "if [ '${DJANGO}' = '1.6.x' ]; then pip install ${DJANGO_16}; fi"
	@sh -c "if [ '${DJANGO}' = 'dev' ]; then pip install ${DJANGO_DEV}; fi"

	@pip install coverage
	@python -c "from __future__ import print_function;import django;print('Django version:', django.get_version())"
	@echo "Database:" ${DBENGINE}

	export PATH=${CASPERJS_DIR}/bin:$${PATH} && $(MAKE) coverage


clean:
	rm -fr ${BUILDDIR} dist *.egg-info .coverage coverage.xml pytest.xml .cache MANIFEST
	find . -name __pycache__ -o -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf
	find adminactions/locale -name django.mo | xargs rm -f


clonedigger: mkbuilddir
	-clonedigger concurrency -l python -o ${BUILDDIR}/clonedigger.html --fast


docs: mkbuilddir
	mkdir -p ${BUILDDIR}/docs
	sphinx-build -aE docs/source ${BUILDDIR}/docs
ifdef BROWSE
	firefox ${BUILDDIR}/docs/index.html
endif

