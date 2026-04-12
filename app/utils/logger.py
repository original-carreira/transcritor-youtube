import logging

def setup_logger():
    """ Configuração global de logging do sistema."""
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    # CORREÇÃO CRÍTICA: retornar logger
    return logging.getLogger("app")