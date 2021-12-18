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
        message = "Welcome to Gitfitti!<br/>Simply fill in your details and draw whatever you want and we'll make it show on your GitHub profile.<br/>If this is your first time, you will have to authorize us to access your GitHub account.<br/>That's it, go wild! ;)"
        return render_template('main.html', page='Home', action="/", c="message", extra=message, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)

    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    name = request.form['username']
    email = request.form['email']
    repname = request.form['repo']
    auth = request.form['auth']
    repurl = f"https://{name}:{auth}@github.com/{name}/{repname}"
    year = request.form.get('year', None)
    ret = commit.apply_async((name, email, repurl, repname, a,
                 int(request.form['nc']), year))
    task = commit.AsyncResult(ret.id)
    if task.result == -1:
        return render_template('main.html', page='Home', action="/", c="message warn", extra="ERROR! Could not clone the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)
    if task.result == -2:
        return render_template('main.html', page='Home', action="/", c="message warn", extra="ERROR! Could not push to the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)
    return render_template('main.html', page='Home', action="/", c='message', n=3720, extra=' ', profile=f'https://github.com/{name}', name=name, repo=repurl, repname=repname, form=request.form, oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True, progress=True, taskid=task.id)


@app.route('/status/<taskid>')
def status(taskid):
    task = commit.AsyncResult(taskid)
    return {'state': task.state, 'current': task.info.get('current'), 'total': task.info.get('total'), 'status': task.info.get('status')}


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

    return render_template('contribute.html', page='Contribute', action="/contribute/", form=request.form, c='message', extra='Contribution added! Changes will reflect in the GitHub repo when an admin merges your contribution.', oauth_url=f'{oauth_url}&redirect_uri={redirect_uri}&scope=repo', check=True)


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
        logout_user()
        return redirect(url_for('login', ret=403))
    rows = get_user_graffiti(username)
    return render_template('user.html', page=username, action=f"/users/{username}/add/", username=username, rows=rows,  c="message", extra=f"Hi {username}, Welcome to your page!", auth=current_user.auth)


@app.route('/users/<username>/add/', methods=['POST'])
@login_required
def add(username):
    if current_user.get_id() != username:
        logout_user()
        return redirect(url_for('login', ret=403))
    a = request.json['a']
    rows = add_graffiti(username, request.json['alias'], request.json['repo'], a, request.json['nc'])
    return "sett", 200


@app.route('/users/<username>/apply/', methods=['POST'])
@login_required
def apply(username):
    if current_user.get_id() != username:
        logout_user()
        return redirect(url_for('login', ret=403))
    a = request.json['a']
    headers = {
        'Authorization': 'token '+current_user.auth
    }
    repurl = f"https://{username}:{current_user.auth}@github.com/{username}/{request.json['repo']}"
    requests.delete(
        f'https://api.github.com/repos/{username}/{request.json["repo"]}', headers=headers)
    data = json.dumps(
        {"name": request.json['repo'], "description": "A repo for GitHub graffiti"})
    requests.post('https://api.github.com/user/repos',
                    headers=headers, data=data)
    ret = commit.apply_async((username, current_user.email, repurl, request.json['repo'], a, int(request.json['nc']), None))
    return {"taskid": ret.id}


@app.route('/users/<username>/<alias>/', methods=['POST'])
@login_required
def modify(username, alias):
    if current_user.get_id() != username:
        logout_user()
        return redirect(url_for('login', ret=403))
    a = request.json['a']
    rows = update_graffiti(username, alias, request.json['alias'], request.json['repo'], a, request.json['nc'])
    return "sett", 200


@app.route('/users/<username>/delete/<alias>/', methods=['GET', 'POST'])
@login_required
def delete(username, alias):
    if current_user.get_id() != username:
        logout_user()
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


# @celery.task(bind=True)
# def massCommit(self, everything):
#     i = 0
#     total = len(everything)
#     for name, email, auth, repo, a, nc in everything:
#         auth = fernet.decrypt(auth.encode()).decode()
#         headers = {
#             'Authorization': 'token '+auth
#         }
#         repurl = f"https://{name}:{auth}@github.com/{name}/{repo}"
#         self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'name':name, 'status': f'Deleting {name}\'s {repo}'})
#         requests.delete(
#             f'https://api.github.com/repos/{name}/{repo}', headers=headers)
#         self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'name':name, 'status': f'Creating {repo} for {name}'})
#         data = json.dumps(
#             {"name": repo, "description": "A repo for GitHub graffiti"})
#         requests.post('https://api.github.com/user/repos',
#                         headers=headers, data=data)
#         ret = commit.apply_async((name, email, repurl, repo, a, nc))
#         self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'name':name, 'status': f'Creating commits in {repo}', 'target': ret.id})
#         i += 1
#     return {'current': total, 'total': total, 'status': 'Complete!', 'result': 'Success!'}


@app.route('/refresh/')
def refresh():
    everything = get_everything()
    total = len(everything)
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
        ret = commit.apply_async((name, email, repurl, repo, a, nc))
    return f"{total} repos... I got it from here ;)"


# @app.route('/refstatus/<taskid>/')
# def refstatus(taskid):
#     task = celery.AsyncResult(taskid)
#     response = {
#         'state': task.state,
#         'current': task.info.get('current', 0),
#         'total': task.info.get('total', 1),
#         'name': task.info.get('name', ''),
#         'status': task.info.get('status', '')
#     }
#     if 'target' in task.info:
#         response['target'] = task.info['target']
#     return response


@app.errorhandler(404)
def error1(a):
    return make_response(render_template('error.html', page='Error 404', error='404'), 404)


@app.errorhandler(400)
def error2(a):
    return make_response(render_template('error.html', page='Error 400', error='400'), 400)


@app.errorhandler(500)
def error3(a):
    return make_response(render_template('error.html', page='Error 500', error='500'), 500)
