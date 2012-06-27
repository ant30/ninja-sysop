
groups = {
        'example.com': 'db.example.com',
        }

protected_items = {
        'example.com':('mail',
                       'www',
                       '@',
                       ),
        }

reload_command = 'rndc'

htpasswd_file = 'htpasswd'

try:
    from local_settings import *
except:
    pass
