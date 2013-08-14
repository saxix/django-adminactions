from django.core.urlresolvers import reverse
from django_webtest import WebTest


class TestGraph(WebTest):
    urls = 'adminactions.tests.urls'
    fixtures = ['adminactions.json', ]

    def setup(self):
        self.renew_app()

    def test_graph_apply(self):
        url = reverse('admin:auth_user_changelist')
        res = self.app.get(url, user='sax')
        res.form['action'] = 'graph_queryset'
        for i in range(0, 11):
            res.form.set('_selected_action', True, i)
        res = res.form.submit()
        res.form['graph_type'] = 'PieChart'
        res.form['axes_x'] = 'is_staff'
        res = res.form.submit('apply')

    def test_graph_post(self):
        url = reverse('admin:auth_user_changelist')
        res = self.app.get(url, user='sax')
        res.form['action'] = 'graph_queryset'
        for i in range(0, 11):
            res.form.set('_selected_action', True, i)
        res = res.form.submit()
        res.form['graph_type'] = 'PieChart'
        res.form['axes_x'] = 'is_staff'
        res = res.form.submit()
