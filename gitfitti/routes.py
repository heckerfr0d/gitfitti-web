from flask import current_app as app
from flask import render_template, request, make_response
from psycopg2 import sql, connect
import hashlib
from .utilities import *

n = 0
cont = []
DATABASE_URL = os.environ['DATABASE_URL']
conn = connect(DATABASE_URL, sslmode='require')
# conn = connect(dbname="gitfitti")

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('main.html', action="/")

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    name = request.form['username']
    email = request.form['email']
    repurl = "https://" + name + ":" + \
        request.form['password'] + "@" + request.form['repo'][8:]
    repname = repurl.split('/')[-1].split('.')[0]
    year = request.form.get('year', None)
    ret = commit(name, email, repurl, repname, a, int(request.form['nc']), year)
    if ret == -1:
        return render_template('main.html', action="/", extra="ERROR! Could not clone the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form)
    if ret == -2:
        return render_template('main.html', action="/", extra="ERROR! Could not push to the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form)
    return render_template('main.html', action="/", extra=' ', n=ret, profile=f'https://github.com/{name}', name=name, repo=repurl, repname=repname, form=request.form)


@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    global n, cont
    if request.method == 'GET':
        return render_template('contribute.html', action="/contribute")

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    editJS(request.form['alias'], a)

    if request.form['auth']:
        pr_link = openPR(request.form['name'], request.form['alias'], request.form['auth'])
        return render_template('contribute.html', action="/contribute", form=request.form, extra=' ', pr=pr_link)
    else:
        if request.form['name']:
            cont.append(request.form['name'])
        n += 1
    return render_template('contribute.html', action="/contribute", form=request.form, extra='Contribution added! Changes will reflect in the GitHub repo when an admin merges your contribution.')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global n
    if request.method == 'GET':
        return render_template('admin.html', action="/admin", n=n)
    thanks = merge(n, cont)
    extra = f'Merged {n} contributions from {thanks}'
    n = 0
    cont.clear()
    return render_template('admin.html', action="/admin", n=n, extra=extra, form=request.form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', action="/register")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id serial primary key, name text not NULL, password text not NULL, email text not NULL UNIQUE, auth text not NULL)")
    auth = base64.b64encode(
        (request.form['auth'][:20]+'a'+request.form['auth'][20:]).encode('utf-8'))
    try:
        cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} (id serial primary key, repo text, alias text, a INTEGER[][], nc integer)").format(
            sql.Identifier(request.form['name'])))
        cursor.execute("INSERT INTO users (name, password, email, auth) VALUES (%s, %s, %s, %s)", (request.form['name'], hashlib.sha3_512(
            request.form['password'].encode()).hexdigest(), request.form['email'], (auth[:10]+b'a'+auth[10:]).decode('utf-8')))
    except:
        return render_template('register.html', extra='Username already registered!')
    conn.commit()
    cursor.close()
    return render_template("user.html", action=f"/users/{request.form['name']}/add")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', action="/login")
    cursor = conn.cursor()
    cursor.execute("SELECT name, password FROM users WHERE name=%s",
                   (request.form['name'],))
    username, password = cursor.fetchone()
    cursor.close()
    if hashlib.sha3_512(request.form['password'].encode()).hexdigest() == password:
        return render_template("user.html", action=f"/users/{username}/add")
    return render_template('login.html', extra='Invalid username or password!')


@app.route('/refresh')
def refresh():
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, auth FROM users")
    users = cursor.fetchall()
    i = 0
    j = 0
    for name, email, auth in users:
        auth = base64.b64decode(auth[:10]+auth[11:]).decode("utf-8")
        auth = auth[:20]+auth[21:]
        headers = {
            'Authorization': 'token '+auth
        }
        cursor.execute(sql.SQL("SELECT DISTINCT ON (repo) repo, a, nc FROM {} ORDER BY (repo), random()").format(
            sql.Identifier(name)))
        for repo, a, nc in cursor.fetchall():
            j += 1
            repurl = f"https://{name}:{auth}@{repo[8:]}"
            repname = repo.split('/')[-1]
            requests.delete(f'https://api.github.com/repos/{name}/{repname}', headers=headers)
            data = json.dumps({"name":repname, "description":"A repo for GitHub graffiti"})
            requests.post('https://api.github.com/user/repos', headers=headers, data=data)
            ret = commit(name, email, repurl, repname, a, nc)
            if ret > 0:
                i += ret
    return render_template('main.html', extra=f"Created {i} commits across {j} repos for {len(users)} users :)")


@app.route('/users/<username>', methods=['POST'])
def userPage(username):
    # cursor = conn.cursor()
    # cursor.execute("SELECT alias, a from %s", (request.form['name'],))
    # rows = cursor.fetchall()
    # cursor.close()
    # print(rows)
    return render_template('user.html', action=f"/users/{username}/add")


@app.route('/users/<username>/add', methods=['POST'])
def add(username):
    cursor = conn.cursor()
    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]
    cursor.execute(sql.SQL("INSERT INTO {} (repo, alias, a, nc) VALUES (%s, %s, %s, %s)").format(
        sql.Identifier(username)), (request.form['repo'], request.form['alias'], a, request.form['nc']))
    conn.commit()
    cursor.close()
    return render_template('user.html', action=f"/users/{username}/add", extra=f"Added '{request.form['alias']}' to the list! :)")


@app.errorhandler(404)
def error1(a):
    return make_response(render_template('error.html', error='404'), 404)
@app.errorhandler(400)
def error2(a):
    return make_response(render_template('error.html', error='400'), 400)
@app.errorhandler(500)
def error3(a):
    return make_response(render_template('error.html', error='500'), 500)