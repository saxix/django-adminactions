BUILDDIR="~build"
#SHELL=/bin/bash

test:
	cd demo && DISABLE_SELENIUM=1 ./manage.py test adminactions

selenium:
	cd demo && ./manage.py test adminactions


clean:
	rm -fr .cache ${BUILDDIR}


docs:
	mkdir -p ${BUILDDIR}/docs
	sphinx-build docs/source ${BUILDDIR}/docs
ifdef OPENDOCS
	firefox ${BUILDDIR}/docs/index.html
endif


.PHONY: docs test
