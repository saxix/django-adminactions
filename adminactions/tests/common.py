import os
from django.conf import global_settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.test.testcases import TestCase
from adminactions.signals import adminaction_requested, adminaction_end, adminaction_start

TEST_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), os.pardir, 'tests', 'templates')
SETTINGS = {'MIDDLEWARE_CLASSES': global_settings.MIDDLEWARE_CLASSES,
            'TEMPLATE_DIRS': [TEST_TEMPLATES_DIR],
            'AUTHENTICATION_BACKENDS': ('django.contrib.auth.backends.ModelBackend',),
            'TEMPLATE_LOADERS': ('django.template.loaders.filesystem.Loader',
                                 'django.template.loaders.app_directories.Loader'),
            # 'AUTH_PROFILE_MODULE': None,
            'TEMPLATE_CONTEXT_PROCESSORS': ("django.contrib.auth.context_processors.auth",
                                            "django.core.context_processors.debug",
                                            "django.core.context_processors.i18n",
                                            "django.core.context_processors.media",
                                            "django.core.context_processors.static",
                                            "django.core.context_processors.request",
                                            "django.core.context_processors.tz",
                                            "django.contrib.messages.context_processors.messages")}


class BaseTestCaseMixin(object):
    urls = 'adminactions.tests.urls'
    fixtures = ['adminactions.json', ]

    def setUp(self):
        super(BaseTestCaseMixin, self).setUp()
        self.sett = self.settings(**SETTINGS)
        self.sett.enable()
        self.login()

    def tearDown(self):
        self.sett.disable()

    def login(self, username='sax', password='123'):
        logged = self.client.login(username=username, password=password)
        assert logged, 'Unable login with credentials'
        self._user = authenticate(username=username, password=password)

    def add_permission(self, *perms, **kwargs):
        """ add the right permission to the user """
        target = kwargs.pop('user', self._user)
        if hasattr(target, '_perm_cache'):
            del target._perm_cache
        for perm_name in perms:
            app_label, code = perm_name.split('.')
            if code == '*':
                perms = Permission.objects.filter(content_type__app_label=app_label)
            else:
                perms = Permission.objects.filter(codename=code, content_type__app_label=app_label)
            target.user_permissions.add(*perms)

        target.save()

    # def assert_post_form(self, response, context_forms=None):
    #     """Assert that a POST response was successful
    #
    #     otherwise raise self.failureException with the forms errors,
    #     or other access denied or redirection errors
    #     """
    #     ctx_forms = context_forms or ['form']
    #     if response.status_code == 200:
    #         msgs = []
    #         for form_name in ctx_forms:
    #             form = response.context[form_name]
    #             if not form.is_valid():
    #                 errors = form.errors
    #                 if errors:
    #                     msgs.append(str(errors))
    #                 if hasattr(form, 'non_form_errors'):
    #                     non_form_errors = form.non_form_errors()
    #                     if non_form_errors:
    #                         msgs.append(str(non_form_errors))
    #         raise self.failureException("\n".join(msgs))
    #     elif response.status_code == 403:
    #         msg = "Access denied for user {0} to url `{1}`".format(self.logged_user, response.request['PATH_INFO'])
    #         raise self.failureException(msg)
    #     elif response.status_code != 302:
    #         raise self.failureException(
    #             'Response did not redirect properly. status_code was %i' % response.status_code)
    #
    # assertPostForm = assert_post_form


class BaseTestCase(BaseTestCaseMixin, TestCase):
    pass


class CheckSignalsMixin(object):
    MESSAGE = 'Action Interrupted Test'
    SELECTION = [2, 3, 4]

    # def test_signal_sent(self):
    #     def handler_factory(name):
    #         def myhandler(sender, action, request, queryset, **kwargs):
    #             handler_factory.invoked[name] = True
    #             self.assertEqual(action, self.action_name)
    #             self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), self.selected_rows)
    #         return myhandler
    #     handler_factory.invoked = {}
    #
    #     try:
    #         m1 = handler_factory('adminaction_requested')
    #         adminaction_requested.connect(m1, sender=self.sender_model)
    #
    #         m2 = handler_factory('adminaction_start')
    #         adminaction_start.connect(m2, sender=self.sender_model)
    #
    #         m3 = handler_factory('adminaction_end')
    #         adminaction_end.connect(m3, sender=self.sender_model)
    #
    #         self._run_action()
    #         self.assertIn('adminaction_requested', handler_factory.invoked)
    #         self.assertIn('adminaction_start', handler_factory.invoked)
    #         self.assertIn('adminaction_end', handler_factory.invoked)
    #
    #     finally:
    #         adminaction_requested.disconnect(m1, sender=self.sender_model)
    #         adminaction_start.disconnect(m2, sender=self.sender_model)
    #         adminaction_end.disconnect(m3, sender=self.sender_model)


#    def test_signal_requested(self):
#        # test if adminaction_requested Signal can stop the action
#
#        def myhandler(sender, action, request, queryset, **kwargs):
#            myhandler.invoked = True
#            self.assertEqual(action, self.action_name)
#            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), self.selected_rows)
#            raise ActionInterrupted(self.MESSAGE)
#
#        try:
#            adminaction_requested.connect(myhandler, sender=Permission)
#            response = self._run_action(code2=302)
#            self.assertTrue(myhandler.invoked)
#            self.assertIn(self.MESSAGE, response.cookies['messages'].value)
#        finally:
#            adminaction_requested.disconnect(myhandler, sender=Permission)
#
#    def test_signal_start(self):
#        # test if adminaction_start Signal can stop the action
#
#        def myhandler(sender, action, request, queryset, form, **kwargs):
#            myhandler.invoked = True
#            self.assertEqual(action, self.action_name)
#            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), self.selected_rows)
#            self.assertTrue(isinstance(form, Form))
#            raise ActionInterrupted(self.MESSAGE)
#
#        try:
#            adminaction_start.connect(myhandler, sender=Permission)
#            response = self._run_action(code3=302)
#            self.assertTrue(myhandler.invoked)
#            self.assertIn(MESSAGE, response.cookies['messages'].value)
#        finally:
#            adminaction_start.disconnect(myhandler, sender=Permission)
#
#    def test_signal_end(self):
#        # test if adminaction_start Signal can stop the action
#
#        def myhandler(sender, action, request, queryset, **kwargs):
#            myhandler.invoked = True
#            self.assertEqual(action, self.action_name)
#            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), self.selected_rows)
#
#        try:
#            adminaction_end.connect(myhandler, sender=Permission)
#            response = self._run_action(code3=200)
#            self.assertTrue(myhandler.invoked)
#        finally:
#            adminaction_end.disconnect(myhandler, sender=Permission)
