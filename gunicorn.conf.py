# Gunicorn — CPEH Fase II ROJO
import multiprocessing

bind = "127.0.0.1:8000"
workers = min(4, multiprocessing.cpu_count() * 2 + 1)
# Fichas con muchas fotos/metrados o subida lenta (móvil) superaban 120s → WORKER TIMEOUT / 500
timeout = 300
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
capture_output = True
