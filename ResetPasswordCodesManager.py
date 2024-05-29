import threading
import time
from RandomStringGenerator import RandomStringGenerator
from Email import Email

class ResetPasswordCodesManager():
    email_code_map = {}
    EXPIRATION_TIME = 3600


    def __init__(self):
        self.lock = threading.Lock()
        thread = threading.Thread(target=self.remove_expired_codes_thread)
        thread.daemon = True
        thread.start()


    def generate_and_send_reset_code_for_email(self, email_address):
        passwordGenerator = RandomStringGenerator()
        code = passwordGenerator.generate_random_string(length=6)
        email = Email(email_address, f"Codul dvs. de resetare a parolei este: {code}")
        email.send()
        print(f"Codul dvs. de resetare a parolei este: {code}")
        with self.lock:
            self.email_code_map[email_address] = {'code': code, 'expiration_time': time.time() + self.EXPIRATION_TIME}


    def is_reset_code_valid(self, email, code):
        with self.lock:
            if email in self.email_code_map:
                code_info = self.email_code_map[email]
                if code_info['code'] == code and code_info['expiration_time'] >= time.time():
                    del self.email_code_map[email]
                    return True
        return False


    def remove_expired_codes_thread(self):
        while True:
            time.sleep(60)
            self.remove_expired_codes()


    def remove_expired_codes(self):
        current_time = time.time()
        with self.lock:
            expired_emails = [email for email, code_information in self.email_code_map.items() if code_information['expiration_time'] < current_time]
            for email in expired_emails:
                del self.email_code_map[email]