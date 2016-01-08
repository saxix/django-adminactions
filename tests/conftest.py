import django_webtest
import pytest


# def pytest_configure(config):
#     try:
#         from django.apps import AppConfig  # noqa
#         import django
#
#         django.setup()
#     except ImportError:
#         pass

def pytest_addoption(parser):
    group = parser.getgroup("selenium", "Selenium Web Browser Automation")
    group.addoption(
        "--selenium-enable", action='store_true', dest='selenium_enable',
        default=False,
        help="launch Selenium tests on hub"
    )

    group.addoption(
        "--chrome-driver", metavar="PATH",
        help="specify the full path for the chromedriver stored in your system. This is a mandatory field "
             "to let start Selenium tests even with Chrome. Command line sample: "
             "py.test --selenium-enable --chrome-driver=/home/chromedriver. -k test_name."
    )


def pytest_configure(config):
    # import warnings
    # enable this to removee deprecations
    # warnings.simplefilter('once', DeprecationWarning)

    if config.option.markexpr.find("selenium") < 0 and \
        not config.option.keyword and \
            config.option.keyword.find('selenium') < 0:
        if not config.option.selenium_enable:
            setattr(config.option, 'markexpr', 'not selenium')


@pytest.fixture(scope='function')
def app(request):
    wtm = django_webtest.WebTestMixin()
    wtm.csrf_checks = False
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    return django_webtest.DjangoTestApp()


@pytest.fixture(scope='function')
def users():
    from django.contrib.auth.models import User
    from django_dynamic_fixture import G

    return G(User, n=2, is_staff=False, is_active=False)


@pytest.fixture(scope='function')
def demomodels():
    from django_dynamic_fixture import G
    from demo.models import DemoModel

    return G(DemoModel, n=20)


@pytest.fixture(scope='function')
def admin():
    from django_dynamic_fixture import G
    from django.contrib.auth.models import User

    return G(User, is_staff=True, is_active=True)


@pytest.fixture(scope='function')
def administrator():
    from django.contrib.auth.models import User
    from utils import ADMIN, PWD

    superuser = User._default_manager.create_superuser(username=ADMIN,
                                                       password=PWD,
                                                       email="sax@noreply.org")
    return superuser
