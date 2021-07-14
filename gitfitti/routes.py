from flask import current_app as app
from flask import render_template, request, make_response
from flask.helpers import url_for
from psycopg2 import sql, connect
from flask_login import login_user, logout_user, current_user, login_required
from cryptography.fernet import Fernet
import base64
import hashlib

from werkzeug.utils import redirect
from .user import User
from .utilities import *

n = 0
cont = []
DATABASE_URL = os.getenv('DATABASE_URL')
conn = connect(DATABASE_URL, sslmode='require')
fernet = Fernet(app.config['SECRET_KEY'])
# conn = connect(dbname="gitfitti")


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('main.html', page='Home', action="/")

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    name = request.form['username']
    email = request.form['email']
    repname = request.form['repo']
    repurl = f"https://{name}:{request.form['password']}@github.com/{name}/{repname}"
    year = request.form.get('year', None)
    ret = commit(name, email, repurl, repname, a,
                 int(request.form['nc']), year)
    if ret == -1:
        return render_template('main.html', page='Home', action="/", c="message warn", extra="ERROR! Could not clone the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form)
    if ret == -2:
        return render_template('main.html', page='Home', action="/", c="message warn", extra="ERROR! Could not push to the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form)
    return render_template('main.html', page='Home', action="/", c='message', extra=' ', n=ret, profile=f'https://github.com/{name}', name=name, repo=repurl, repname=repname, form=request.form)


@app.route('/contribute/', methods=['GET', 'POST'])
def contribute():
    global n, cont
    if request.method == 'GET':
        return render_template('contribute.html', page='Contribute', action="/contribute")

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    editJS(request.form['alias'], a)

    if request.form['auth']:
        pr_link = openPR(
            request.form['name'], request.form['alias'], request.form['auth'])
        return render_template('contribute.html', page='Contribute', action="/contribute", form=request.form, c='message', extra=' ', pr=pr_link)
    else:
        if request.form['name']:
            cont.append(request.form['name'])
        n += 1
    return render_template('contribute.html', page='Contribute', action="/contribute", form=request.form, c='message', extra='Contribution added! Changes will reflect in the GitHub repo when an admin merges your contribution.')


@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    global n
    if request.method == 'GET':
        return render_template('admin.html', page='Admin', action="/admin", n=n)
    thanks = merge(n, cont)
    extra = f'Merged {n} contributions from {thanks}'
    n = 0
    cont.clear()
    return render_template('admin.html', page='Admin', action="/admin", n=n, c='message', extra=extra, form=request.form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', page='Register', action="/register")
    cursor = conn.cursor()
    try:
        name = request.form['name']
        email = request.form['email']
        cursor.execute(sql.SQL("CREATE TABLE {} (id serial primary key, repo text, alias text, a INTEGER[][], nc integer)").format(
            sql.Identifier(name)))
        password = hashlib.sha3_512(
            request.form['password'].encode()).hexdigest()
        auth = fernet.encrypt(request.form['auth'].encode()).decode()
        cursor.execute("INSERT INTO users (name, password, email, auth) VALUES (%s, %s, %s, %s)",
                       (name, password, email, auth))
        user = User(name, email, password, auth)
        if current_user.is_authenticated:
            logout_user()
        login_user(user, remember=True)
    except:
        return render_template('register.html', page='Register', action="/register", c='message warn', extra='Invalid details or user already registered!')
    conn.commit()
    cursor.close()
    return redirect(url_for('userPage', username=name))


@app.route('/login/', methods=['GET', 'POST'])
@app.route('/login/<ret>/', methods=['GET', 'POST'])
def login(ret=None):
    if current_user.is_authenticated:
        return redirect(url_for('userPage', username=current_user.get_id()))
    if ret:
        return render_template('login.html', page='Login', action='/login', c='message warn', extra='You have to be logged in to access that page!')
    if request.method == 'GET':
        return render_template('login.html', page='Login', action="/login")
    cursor = conn.cursor()
    cursor.execute("SELECT name, password, email, auth FROM users WHERE name=%s",
                   (request.form['name'],))
    username, password, email, auth = cursor.fetchone()
    cursor.close()
    if hashlib.sha3_512(request.form['password'].encode()).hexdigest() == password:
        user = User(username, email, password, auth)
        login_user(user, remember=True)
        return redirect(url_for('userPage', username=username))
    return render_template('login.html', page='Login', action='/login', c='message warn', extra='Invalid username or password!')


@app.route('/users/<username>/', methods=['GET', 'POST'])
@login_required
def userPage(username):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=True))
    cursor = conn.cursor()
    cursor.execute(sql.SQL("SELECT alias, repo, a, nc FROM {}").format(
        sql.Identifier(username)))
    rows = cursor.fetchall()
    cursor.close()
    return render_template('user.html', page=username, action=f"/users/{username}/add", username=username, rows=rows,  c="message", extra=f"Hi {username}, Welcome to your page!")


@app.route('/users/<username>/add/', methods=['POST'])
@login_required
def add(username):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=True))
    cursor = conn.cursor()
    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]
    cursor.execute(sql.SQL("INSERT INTO {} (repo, alias, a, nc) VALUES (%s, %s, %s, %s)").format(
        sql.Identifier(username)), (request.form['repo'], request.form['alias'], a, request.form['nc']))
    conn.commit()
    cursor.execute(sql.SQL("SELECT alias, repo, a, nc FROM {}").format(
        sql.Identifier(username)))
    rows = cursor.fetchall()
    cursor.close()
    return render_template('user.html', page=username, action=f"/users/{username}/add", c="message", extra=f"Added '{request.form['alias']}' to the list!", username=username, rows=rows)


@app.route('/users/<username>/<alias>/', methods=['POST'])
@login_required
def modify(username, alias):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=True))
    cursor = conn.cursor()
    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]
    cursor.execute(sql.SQL("SELECT id FROM {} WHERE alias=%s").format(
        sql.Identifier(username)), (alias,))
    id = cursor.fetchone()
    cursor.execute(sql.SQL("UPDATE {} SET alias=%s, repo=%s, a=%s, nc=%s where id=%s").format(
        sql.Identifier(username)), (request.form['alias'], request.form['repo'], a, request.form['nc'], id))
    conn.commit()
    cursor.execute(sql.SQL("SELECT alias, repo, a, nc FROM {}").format(
        sql.Identifier(username)))
    rows = cursor.fetchall()
    cursor.close()
    return render_template('user.html', page=username, action=f"/users/{username}/add", c="message", extra="List Updated!", username=username, rows=rows)


@app.route('/users/<username>/delete/<alias>/', methods=['GET', 'POST'])
@login_required
def delete(username, alias):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=True))
    cursor = conn.cursor()
    cursor.execute(sql.SQL("SELECT id FROM {} WHERE alias=%s").format(
        sql.Identifier(username)), (alias,))
    id = cursor.fetchone()
    cursor.execute(sql.SQL("DELETE FROM {} WHERE id=%s").format(
        sql.Identifier(username)), (id,))
    conn.commit()
    cursor.execute(sql.SQL("SELECT alias, repo, a, nc FROM {}").format(
        sql.Identifier(username)))
    rows = cursor.fetchall()
    cursor.close()
    return render_template('user.html', page=username, action=f"/users/{username}/add", c="message", extra=f"Removed '{alias}' from the list!", username=username, rows=rows)


@app.route('/users/delete/<username>/', methods=['GET', 'POST'])
@login_required
def deleteUser(username):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=True))
    cursor = conn.cursor()
    cursor.execute(sql.SQL("DROP TABLE {}").format(
        sql.Identifier(username)))
    cursor.execute("DELETE FROM users WHERE name=%s", (username,))
    conn.commit()
    cursor.close()
    logout_user(current_user)
    return redirect(url_for('login', ret=True))

@app.login_manager.user_loader
def user_loader(user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, email, password, auth FROM users WHERE name=%s", (user_id,))
    try:
        name, email, password, auth = cursor.fetchone()
        cursor.close()
        return User(name, email, password, auth)
    except:
        return None


@app.login_manager.unauthorized_handler
def unauth():
    return redirect(url_for('login', ret=True))


@app.route('/refresh/')
def refresh():
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, auth FROM users")
    users = cursor.fetchall()
    i = 0
    j = 0
    for name, email, auth in users:
        auth = fernet.decrypt(auth.encode()).decode()
        headers = {
            'Authorization': 'token '+auth
        }
        cursor.execute(sql.SQL("SELECT DISTINCT ON (repo) repo, a, nc FROM {} ORDER BY (repo), random()").format(
            sql.Identifier(name)))
        for repo, a, nc in cursor.fetchall():
            j += 1
            repurl = f"https://{name}:{auth}@github.com/{name}/{repo}"
            requests.delete(
                f'https://api.github.com/repos/{name}/{repo}', headers=headers)
            data = json.dumps(
                {"name": repo, "description": "A repo for GitHub graffiti"})
            requests.post('https://api.github.com/user/repos',
                          headers=headers, data=data)
            ret = commit(name, email, repurl, repo, a, nc)
            if ret > 0:
                i += ret
    cursor.close()
    return render_template('main.html', page='Home', action="/", c='message', extra=f"Created {i} commits across {j} repos for {len(users)} users :)")


@app.errorhandler(404)
def error1(a):
    return make_response(render_template('error.html', page='Error 404', error='404'), 404)


@app.errorhandler(400)
def error2(a):
    return make_response(render_template('error.html', page='Error 400', error='400'), 400)


@app.errorhandler(500)
def error3(a):
    return make_response(render_template('error.html', page='Error 500', error='500'), 500)
