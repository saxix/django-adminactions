try:
    from django.db.transaction import atomic
    import django.db.transaction as t

except:
    from django.db.transaction import commit_on_success as atomic, rollback, commit_manually
    import django.db.transaction as t
