VERSION=2.0.0
BUILDDIR=${PWD}/~build
BINDIR=${PWD}/~build/bin
PYTHONPATH:=${PWD}/tests/:${PWD}
DJANGO?='1.7.x'

mkbuilddir:
	mkdir -p ${BUILDDIR} ${BINDIR}


install-deps:
	pip install -e .
	pip install -r adminactions/requirements/testing.pip
	@sh -c "if [ '${DJANGO}' = '1.4.x' ]; then pip install 'django>=1.4,<1.5'; fi"
	@sh -c "if [ '${DJANGO}' = '1.5.x' ]; then pip install 'django>=1.5,<1.6'; fi"
	@sh -c "if [ '${DJANGO}' = '1.6.x' ]; then pip install 'django>=1.6,<1.7'; fi"
	@sh -c "if [ '${DJANGO}' = '1.7.x' ]; then pip install 'django>=1.7,<1.8'; fi"
	@sh -c "if [ '${DJANGO}' = '1.8.x' ]; then pip install 'django>=1.8,<1.9'; fi"
	@sh -c "if [ '${DJANGO}' = 'dev' ]; then pip install git+git://github.com/django/django.git; fi"



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


coverage: mkbuilddir install-deps init-db
	echo ${PYTHONPATH};
	PYTHONPATH=${PWD}/tests/:${PWD} py.test tests -v --cov=adminactions --cov-report=html --cov-config=tests/.coveragerc -q



demo:
	django-admin.py syncdb --settings=tests.settings --noinput
	django-admin.py loaddata adminactions.json demoproject.json --settings=tests.settings
	django-admin.py runserver --settings=tests.settings


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
	psql -c 'DROP DATABASE IF EXISTS adminactions;' -U postgres; fi
	mysql -e 'DROP DATABASE IF EXISTS test_adminactions;';
	psql -c 'DROP DATABASE IF EXISTS test_adminactions;' -U postgres; fi


clonedigger: mkbuilddir
	-clonedigger concurrency -l python -o ${BUILDDIR}/clonedigger.html --fast


docs: mkbuilddir
	mkdir -p ${BUILDDIR}/docs
	sphinx-build -aE docs/source ${BUILDDIR}/docs
ifdef BROWSE
	firefox ${BUILDDIR}/docs/index.html
endif

