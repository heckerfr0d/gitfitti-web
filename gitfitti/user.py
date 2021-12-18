from flask import current_app
from psycopg2 import connect
from cryptography.fernet import Fernet

fernet = Fernet(current_app.config['SECRET_KEY'])
DATABASE_URL = current_app.config['DATABASE_URL']
conn = connect(DATABASE_URL, sslmode='require')
# conn = connect(dbname='gitfitti')


class User:
    def __init__(self, name, password, email, auth):
        self.name = name
        self.password = password
        self.email = email
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

def get_user(username):
    cur = conn.cursor()
    cur.execute("SELECT name, password, email, auth FROM users WHERE name = %s", (username,))
    user = cur.fetchone()
    cur.close()
    if not user:
        return None
    if user[3]:
        auth = fernet.decrypt(user[3].encode()).decode()
    else:
        auth = None
    return User(user[0], user[1], user[2], auth)

def add_user(username, password, email):
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, password, email) VALUES (%s, %s, %s)", (username, password, email))
    conn.commit()
    cur.close()
    return User(username, password, email, None)

def update_auth(username, auth):
    cur = conn.cursor()
    auth = fernet.encrypt(auth.encode()).decode()
    cur.execute("UPDATE users SET auth = %s WHERE name = %s", (auth, username))
    conn.commit()
    cur.close()
    return True

def get_user_graffiti(username):
    cur = conn.cursor()
    cur.execute("SELECT alias, repo, a, nc, year FROM graffiti WHERE name = %s", (username,))
    graffiti = cur.fetchall()
    cur.close()
    return graffiti

def add_graffiti(username, alias, repo, a, nc, year):
    cur = conn.cursor()
    cur.execute("INSERT INTO graffiti (name, alias, repo, a, nc, year) VALUES (%s, %s, %s, %s, %s, %s)", (username, alias, repo, a, nc, year))
    conn.commit()
    cur.close()
    return get_user_graffiti(username)

def update_graffiti(username, oldalias, newalias, repo, a, nc, year):
    cur = conn.cursor()
    cur.execute("UPDATE graffiti SET alias = %s, repo = %s, a = %s, nc = %s, year = %s WHERE name = %s AND alias = %s", (newalias, repo, a, nc, year, username, oldalias))
    conn.commit()
    cur.close()
    return get_user_graffiti(username)

def delete_graffiti(username, alias):
    cur = conn.cursor()
    cur.execute("DELETE FROM graffiti WHERE name = %s AND alias = %s", (username, alias))
    conn.commit()
    cur.close()
    return get_user_graffiti(username)

def delete_user(username):
    cur = conn.cursor()
    cur.execute("DELETE FROM graffiti WHERE name = %s", (username,))
    cur.execute("DELETE FROM users WHERE name = %s", (username,))
    conn.commit()
    cur.close()
    return True

def get_old(username, repo):
    cur = conn.cursor()
    cur.execute("SELECT u.name, u.email, u.auth, g.repo, g.a, g.nc, g.year FROM users u, graffiti g WHERE u.name = g.name AND g.year IS NOT NULL AND u.name = %s AND g.repo = %s", (username, repo))
    oldies = cur.fetchall()
    cur.close()
    return oldies

def get_everything():
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT ON (g.name, g.repo) u.name, u.email, u.auth, g.repo, g.a, g.nc, g.year FROM users u, graffiti g WHERE u.name = g.name AND g.year IS NULL ORDER BY g.name, g.repo, RANDOM()")
    everything = cur.fetchall()
    cur.close()
    return everything