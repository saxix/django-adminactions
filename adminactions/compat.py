try:
    from django.db.transaction import atomic, rollback
except:  # django<1.6
    from django.db.transaction import commit_on_success as atomic, rollback
