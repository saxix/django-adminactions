# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django_dynamic_fixture import G


class Command(BaseCommand):
    args = ''
    help = 'Help text here....'
    """
    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete poll instead of closing it'),
        )
    """

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        from demoproject.demoapp.models import DemoModel,  UserDetail, UserProfile

        for x in range(100):
            G(DemoModel)

        for x in range(10):
            G(UserProfile)
            G(UserDetail)
