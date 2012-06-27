
app = 'bind9'

groups = {
        'example.com': 'examples/bind9/db.example.com',
        }

protected_items = {
        'example.com':('mail',
                       'www',
                       '@',
                       ),
        }

reload_command = 'rndc'

htpasswd_file = 'examples/htpasswd'

try:
    from local_settings import *
except:
    pass
