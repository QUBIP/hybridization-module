# Excepción personalizada para el timeout
class TimeoutException(Exception):
    pass

# Handler de la señal de timeout
def timeout_handler(signum, frame):
    raise TimeoutException()
