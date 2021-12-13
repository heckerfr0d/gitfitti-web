from flask import current_app as app
from flask import render_template, request, make_response
from flask.helpers import url_for
from flask_login import login_user, logout_user, current_user, login_required
import hashlib
from werkzeug.utils import redirect
from .user import *
from .utilities import *

n = 0
cont = []
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
oauth_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}"


@app.route('/', methods=['GET', 'POST'])
def main():
    redirect_uri = url_for('redir', target='done', _external=True)
    if request.method == 'GET':
        return render_template('main.html', page='Home', action="/", oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    name = request.form['username']
    email = request.form['email']
    repname = request.form['repo']
    auth = request.form['auth']
    repurl = f"https://{name}:{auth}@github.com/{name}/{repname}"
    year = request.form.get('year', None)
    ret = commit(name, email, repurl, repname, a,
                 int(request.form['nc']), year)
    if ret == -1:
        return render_template('main.html', page='Home', action="/", c="message warn", extra="ERROR! Could not clone the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)
    if ret == -2:
        return render_template('main.html', page='Home', action="/", c="message warn", extra="ERROR! Could not push to the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)
    return render_template('main.html', page='Home', action="/", c='message', extra=' ', n=ret, profile=f'https://github.com/{name}', name=name, repo=repurl, repname=repname, form=request.form, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)


@app.route('/contribute/', methods=['GET', 'POST'])
def contribute():
    global n, cont
    redirect_uri = url_for('redir', target='done', _external=True)
    if request.method == 'GET':
        return render_template('contribute.html', page='Contribute', action="/contribute/", oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    editJS(request.form['alias'], a)

    if request.form['auth']:
        pr_link = openPR(request.form['name'], request.form['alias'], request.form['auth'])
        return render_template('contribute.html', page='Contribute', action="/contribute/", form=request.form, c='message', extra=' ', pr=pr_link, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)
    else:
        if request.form['name']:
            cont.append(request.form['name'])
        n += 1
    return render_template('contribute.html', page='Contribute', action="/contribute/", form=request.form, c='message', extra='Contribution added! Changes will reflect in the GitHub repo when an admin merges your contribution.', oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)


@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    global n
    if request.method == 'GET':
        return render_template('admin.html', page='Admin', action="/admin/", n=n)
    thanks = merge(n, cont)
    extra = f'Merged {n} contributions from {thanks}'
    n = 0
    cont.clear()
    return render_template('admin.html', page='Admin', action="/admin/", n=n, c='message', extra=extra, form=request.form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', page='Register', action="/register/")
    name = request.form['name']
    email = request.form['email']
    password = hashlib.sha3_512(request.form['password'].encode()).hexdigest()
    if not get_user(name):
        logout_user()
        login_user(add_user(name, password, email), remember = True)
    else:
        return render_template('register.html', page='Register', action="/register/", c='message warn', extra='Invalid details or user already registered!')
    redirect_uri = url_for("redir", target='register', _external=True)
    return redirect(oauth_url+f'&redirect_uri={redirect_uri}&scope=repo+delete_repo')


@app.route('/login/', methods=['GET', 'POST'])
@app.route('/login/<ret>/', methods=['GET', 'POST'])
def login(ret=None):
    if current_user.is_authenticated:
        return redirect(url_for('userPage', username=current_user.get_id()))
    if ret:
        return render_template('login.html', page='Login', action='/login/', c='message warn', extra='You have to be logged in to access that page!')
    if request.method == 'GET':
        return render_template('login.html', page='Login', action="/login/")
    user = get_user(request.form['name'])
    if hashlib.sha3_512(request.form['password'].encode()).hexdigest() == user.password:
        login_user(user, remember=True)
        return redirect(url_for('userPage', username=user.get_id()))
    return render_template('login.html', page='Login', action='/login/', c='message warn', extra='Invalid username or password!')


@app.route('/redirect/<target>', methods=['GET', 'POST'])
def redir(target):
    headers = {'Accept':'application/json'}
    code = request.args.get('code')
    if code:
        data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': code, 'redirect_uri': url_for("redir", target=target, _external=True)}
        resp = requests.post("https://github.com/login/oauth/access_token", data=data, headers=headers).json()
        if target == 'register':
            update_auth(current_user.get_id(), resp['access_token'])
            return redirect(url_for('userPage', username=current_user.get_id()))
        elif target == 'done':
            return render_template('done.html', page='Authorized', action='/', c='message', extra='Successfully authorized!', auth=resp['access_token'])
    else:
        if target == 'register':
            username = current_user.get_id()
            logout_user()
            delete_user(username)
            return redirect(url_for('register'))
        elif target == 'done':
            return redirect(url_for('main'))



@app.route('/users/<username>/', methods=['GET', 'POST'])
@login_required
def userPage(username):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=403))
    rows = get_user_graffiti(username)
    return render_template('user.html', page=username, action=f"/users/{username}/add/", username=username, rows=rows,  c="message", extra=f"Hi {username}, Welcome to your page!", auth=current_user.auth)


@app.route('/users/<username>/add/', methods=['POST'])
@login_required
def add(username):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=403))
    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]
    rows = add_graffiti(username, request.form['alias'], request.form['repo'], a, request.form['nc'])
    return render_template('user.html', page=username, action=f"/users/{username}/add/", c="message", extra=f"Added '{request.form['alias']}' to the list!", username=username, rows=rows)


@app.route('/users/<username>/<alias>/', methods=['POST'])
@login_required
def modify(username, alias):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=403))
    cursor = conn.cursor()
    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]
    rows = update_graffiti(username, alias, request.form['repo'], a, request.form['nc'])
    return render_template('user.html', page=username, action=f"/users/{username}/add/", c="message", extra="List Updated!", username=username, rows=rows)


@app.route('/users/<username>/delete/<alias>/', methods=['GET', 'POST'])
@login_required
def delete(username, alias):
    if current_user.get_id() != username:
        logout_user(current_user)
        return redirect(url_for('login', ret=403))
    rows = delete_graffiti(username, alias)
    return render_template('user.html', page=username, action=f"/users/{username}/add/", c="message", extra=f"Removed '{alias}' from the list!", username=username, rows=rows)


@app.route('/users/delete/<username>/', methods=['GET', 'POST'])
@login_required
def deleteUser(username):
    if current_user.get_id() != username:
        logout_user()
        return redirect(url_for('login', ret=403))
    username = current_user.get_id()
    logout_user()
    delete_user(username)
    return redirect(url_for('login'))

@app.login_manager.user_loader
def user_loader(user_id):
    return get_user(user_id)


@app.login_manager.unauthorized_handler
def unauth():
    return redirect(url_for('login', ret=403))


@app.route('/refresh/')
def refresh():
    everything = get_everything()
    i = 0
    for name, email, auth, repo, a, nc in everything:
        auth = fernet.decrypt(auth.encode()).decode()
        headers = {
            'Authorization': 'token '+auth
        }
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
        print(ret)
    return render_template('main.html', page='Home', action="/", c='message', extra=f"Created {i} commits across {len(everything)} repos for {len(everything)} users :)")


@app.errorhandler(404)
def error1(a):
    return make_response(render_template('error.html', page='Error 404', error='404'), 404)


@app.errorhandler(400)
def error2(a):
    return make_response(render_template('error.html', page='Error 400', error='400'), 400)


@app.errorhandler(500)
def error3(a):
    return make_response(render_template('error.html', page='Error 500', error='500'), 500)
