
import logging
import os
from datetime import date, datetime
import time
import sentry_sdk


class ProgramLog:
    def __init__(self, text_filename="philippian_encoder"):
        super().__init__()
        self.default_path  = None
        # basepath = self.get_userprofile_basepath()
        # self.default_path = f"{basepath}/logs"
        
        # self.create_default_folder()
        
        # # Create a unique log file name
        # log_filename = f"{self.default_path}/logs_{text_filename}_seq_{self.get_timestamp_today()}.log"
        
        # # Create a logger for this instance
        self.logger = logging.getLogger(f"ProgramLog_{text_filename}_{self.get_timestamp_today()}")
        self.logger.setLevel(logging.INFO)
        
        # # Ensure no duplicate handlers for this logger
        # if not self.logger.hasHandlers():
        #     # Create a file handler
        #     file_handler = logging.FileHandler(log_filename, mode="w", encoding="utf-8")
        #     file_handler.setLevel(logging.INFO)
            
        #     # Create a formatter and add it to the handler
        #     formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        #     file_handler.setFormatter(formatter)
            
        #     # Add the handler to the logger
        #     self.logger.addHandler(file_handler)
        
        # print(f"Log file created: {log_filename}")

    def create_default_folder(self):
        if not os.path.exists(self.default_path):
            os.makedirs(self.default_path)

    def default(self):
        self.logger.info("test the logger...")
        message_context = {"message": "test the logger..."}
        # sentry_sdk.capture_message(message_context)

    def write_log_info(self, message):
        self.logger.info(message)
        message_context = {"message": message}
        # sentry_sdk.capture_message(message_context)

    def write_log_error(self, message):
        self.logger.error(message)
        message_context = {"message": message}
        # sentry_sdk.capture_exception(message_context)

    def write_log_critical(self, message):
        self.logger.critical(message)
        message_context = {"message": message}
        # sentry_sdk.capture_exception(message_context)

    def get_userprofile_basepath(self):
        user_profile = os.path.expanduser('~')
        # Define the new folder path
        new_folder_path = os.path.join(user_profile, '.pgocapp')
        return new_folder_path

    @staticmethod
    def get_timestamp_today():
        # Return the current timestamp in a string format
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
