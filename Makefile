VERSION=2.0.0
BUILDDIR=${PWD}/~build
BINDIR=${PWD}/~build/bin
PYTHONPATH:=${PWD}/tests/:${PWD}
DJANGO?='1.7.x'

mkbuilddir:
	mkdir -p ${BUILDDIR}

develop:
	pip install -e .[dev]


demo:
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src django-admin.py migrate --settings=demo.settings --noinput
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src  django-admin.py loaddata adminactions.json demoproject.json --settings=demo.settings
	PYTHONPATH=${PWD}:${PWD}/tests:${PWD}/src  django-admin.py runserver --settings=demo.settings


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

