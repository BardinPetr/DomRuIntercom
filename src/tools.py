import base64
import hashlib


def generate_auth_hashes(login, password, date,
                         secret="789sdgHJs678wertv34712376"):
    tmp = f'DigitalHomeNTKpassword{login}{password}{date.strftime("%Y%m%d%H%M%S")}{secret}'
    return [
        base64.b64encode(hashlib.sha1(password.encode('utf-8')).digest()).decode('utf-8'),
        hashlib.md5(tmp.encode('utf-8')).hexdigest()
    ]
