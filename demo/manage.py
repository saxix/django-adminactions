#!/usr/bin/env python
import os, sys

here = os.path.abspath(os.path.join(os.path.dirname(__file__)))
rel = lambda *args: os.path.join(here, *args)

sys.path.insert(0, rel(os.pardir))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demoproject.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
