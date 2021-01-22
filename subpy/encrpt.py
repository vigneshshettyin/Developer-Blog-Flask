from passlib.hash import sha256_crypt

presentPass="admin"
password = sha256_crypt.encrypt(presentPass)
print(len(password))
print(sha256_crypt.verify(presentPass, password))