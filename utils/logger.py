
import os
from services.fileHandler import writeLog

class Logger:
    def __init__(self, log_file="app.log"):
        self.log_file = log_file

    def log(self, message):
        if os.getenv("ENABLE_LOGGING", "false").lower() == "true":
            writeLog(message, self.log_file)

logger = Logger()