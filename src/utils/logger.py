import logging
import os

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance.

    Args:
        name (str): The name of the logger (usually __name__).

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO) # Default logging level

    # Ensure handlers are not duplicated if called multiple times
    if not logger.handlers:
        # Create a console handler
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional: Add a file handler
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger