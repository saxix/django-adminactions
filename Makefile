VERSION=2.0.0
BUILDDIR='~build'
DJANGO_SETTINGS_MODULE:=demoproject.settings
PYTHONPATH := ${PWD}/demo/:${PWD}

CASPERJS_DIR=${BUILDDIR}/casperjs
PHANTOMJS_DIR=${BUILDDIR}/phantomjs

mkbuilddir:
	mkdir -p ${BUILDDIR}

test:
	py.test

selenium:
	cd demo && ./manage.py test adminactions

locale:
	cd adminactions && django-admin.py makemessages -l en
	export PYTHONPATH=${PYTHONPATH} && cd adminactions && django-admin.py compilemessages --settings=${DJANGO_SETTINGS_MODULE}


coverage: mkbuilddir
	py.test --cov=adminactions --cov-report=html --cov-config=.coveragerc



ci:
	@[ "${DJANGO}" = "1.4.x" ] && pip install django==1.4.8 || :
	@[ "${DJANGO}" = "1.5.x" ] && pip install django==1.5.4 || :
	@[ "${DJANGO}" = "1.6.x" ] && pip install https://www.djangoproject.com/m/releases/1.6/Django-1.6b4.tar.gz || :
	#@[ "${DJANGO}" = "dev" ] && pip install git+git://github.com/django/django.git || :

	@[ "${DBENGINE}" = "pg" ] && pip install -q psycopg2 || :
	@[ "${DBENGINE}" = "mysql" ] && pip install git+git@github.com:django/django.git || :

	@pip install coverage -r adminactions/requirements.pip
	@python -c "from __future__ import print_function;import django;print('Django version:', django.get_version())"

	DISABLE_SELENIUM=1 coverage run demo/manage.py test adminactions --settings=demoproject.settings_travis
	coverage report

clean:
	rm -fr ${BUILDDIR} dist *.egg-info .coverage coverage.xml pytest.xml .cache MANIFEST
	find . -name __pycache__ -o -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf
	find adminactions/locale -name django.mo | xargs rm -f

docs: mkbuilddir
	mkdir -p ${BUILDDIR}/docs
	sphinx-build -aE docs/source ${BUILDDIR}/docs
ifdef BROWSE
	firefox ${BUILDDIR}/docs/index.html
endif

