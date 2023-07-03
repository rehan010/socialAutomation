from django.core.management import execute_from_command_line
from pyngrok import ngrok
from django.conf import settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Automatation.settings")
settings.ALLOWED_HOSTS=['*']
# settings.configure()
# Start ngrok tunnel
ngrok.set_auth_token("1yil0KHiUzZGvigFuDVZmUIFdr9_Y1RAquHkpPPjk9e6Wfk9")  # Replace with your ngrok authentication token
# public_url = ngrok.connect(config_path="/Users/apple/.ngrok2/ngrok.yml", options={"bind_tls": True})

public_url = ngrok.connect(8000,options={"bind_tls": True})  # Replace 8000 with the port of your Django development server
print("Public URL:", public_url)

# Run Django server
execute_from_command_line(['manage.py', 'runserver'])
ngrok_process = ngrok.get_ngrok_process()
ngrok_process.proc.wait()