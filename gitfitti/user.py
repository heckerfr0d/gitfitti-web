class User:
    def __init__(self, name, email, password, auth):
        self.name = name
        self.email = email
        self.password = password
        self.auth = auth
        self.authenticated = True

    def is_active(self):
        return True

    def get_id(self):
        return self.name

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False