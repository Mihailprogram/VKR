from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django.db import models
# Miha Тут изменения схемы

@receiver(class_prepared)
def change_db_table(sender, **kwargs):
    from django.conf import settings
    DATABASES = settings.DATABASES
    if issubclass(sender, models.Model):
        db_table = sender._meta.__getattribute__('db_table')
        app_label = sender._meta.model_name
        try:
            scheme = DATABASES[sender.database].get('SCHEME', '')
            sender._meta.db_table = f'"{scheme}"."{db_table}"'
            if sender._meta.many_to_many:
                for m2m_field in sender._meta.many_to_many:
                    through_model = m2m_field.remote_field.through
                    db_table = through_model._meta.db_table
                    through_model.db_table = f'"{scheme}"."{db_table}"'
                    print(through_model.db_table)
        except:
            if db_table.split('_')[0] == 'public' or db_table.split('_')[0] == 'django':
                scheme = 'mkadd'
                sender._meta.db_table = f'"{scheme}"."{db_table}"'
            else:
                print('w/o table')


class_prepared.connect(change_db_table)
