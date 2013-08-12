BUILDDIR=~build
PYTHONPATH := ${PWD}/demo/:${PWD}
DJANGO_SETTINGS_MODULE:=demoproject.settings

mkbuilddir:
	mkdir -p ${BUILDDIR}


test:
	cd demo && DISABLE_SELENIUM=1 ./manage.py test adminactions

selenium:
	cd demo && ./manage.py test adminactions

locale:
	cd adminactions && django-admin.py makemessages -l en
	export PYTHONPATH=${PYTHONPATH} && cd adminactions && django-admin.py compilemessages --settings=${DJANGO_SETTINGS_MODULE}


coverage:
	coverage run demo/manage.py test adminactions
	coverage report

clean:
	rm -fr ${BUILDDIR} dist *.egg-info .coverage coverage.xml pytest.xml .cache MANIFEST
	find . -name __pycache__ -prune | xargs rm -rf
	find . -name "*.py?" -prune | xargs rm -rf
	find . -name "*.orig" -prune | xargs rm -rf
	find adminactions/locale -name django.mo | xargs rm -f

docs: mkbuilddir
	mkdir -p ${BUILDDIR}/docs
	sphinx-build docs/source ${BUILDDIR}/docs
ifdef BROWSE
	firefox ${BUILDDIR}/docs/index.html
endif


.PHONY: docs test
