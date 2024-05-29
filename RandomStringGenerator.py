import secrets
import string

class RandomStringGenerator():
    def generate_random_string(self, length=12):
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password