from flask import Flask, render_template, request
import git
import datetime
import os
import shutil
import requests
import base64
import json

app = Flask(__name__)
n = 0
cont = []


def getDates(year=None):
    if year:
        jan1 = datetime.datetime(
            year=year, month=1, day=1, hour=10, minute=20, second=59)
    else:
        jan1 = datetime.datetime.now() - datetime.timedelta(weeks=53)
        jan1 -= datetime.timedelta(microseconds=jan1.microsecond)

    def onDay(date, day): return date + \
        datetime.timedelta(days=(day-date.weekday()) % 7)
    first_sunday = onDay(jan1, 6)
    dates = [list() for x in range(7)]
    for x in range(52 * 7):
        dates[x % 7].append(first_sunday + datetime.timedelta(x))
    return dates


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('main.html', action="/")
    # a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]
    # text_to_render = request.form['text']
    # font = Font('Fonts/subway-ticker.ttf', 8)
    # try:
    #     text = repr(font.render_text(text_to_render, 52, 7))
    #     text_by_weekday = text.split('\n')
    #     for i in range(7):
    #         for j in range(52):
    #             if text_by_weekday[i][j] == '#':
    #                 a[i][j] = (a[i][j] + 1)%3
    #     return render_template('main.html', a=a)
    # except:
    #     return "error"
    a = [[int(request.form[f'{i} {j}']) for j in range(52)] for i in range(7)]

    def getActiveDates(dates):
        ad = []
        for i in range(7):
            for j in range(52):
                for k in range(a[i][j]):
                    ad.append(dates[i][j])
        return ad
    try:
        year = int(request.form['year'])
        dates = getActiveDates(getDates(year))
    except:
        dates = getActiveDates(getDates())
    name = request.form['username']
    email = request.form['email']
    author = git.Actor(name, email)

    repurl = "https://" + name + ":" + \
        request.form['password'] + "@" + request.form['repo'][8:]
    repname = repurl.split('/')[-1].split('.')[0]
    if not os.path.isdir(repname):
        try:
            git.cmd.Git().clone(repurl)
        except:
            return render_template('main.html', action="/", extra="ERROR! Could not clone the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form)
    rep = git.Repo.init(repname)
    nc = int(request.form['nc'])
    for date in dates:
        for n in range(nc):
            rep.index.commit("made with love by gitfitti", author=author,
                             committer=author, author_date=date.isoformat())
    try:
        rep.remotes.origin.set_url(repurl)
    except:
        rep.create_remote('origin', repurl)
    try:
        rep.remotes.origin.push()
        shutil.rmtree(repname)
    except:
        shutil.rmtree(repname)
        return render_template('main.html', action="/", extra="ERROR! Could not push to the repo. Ensure that the remote repo exists and that you have access to it.", form=request.form)
    return render_template('main.html', action="/", extra=f'SUCCESS! Created {nc*len(dates)} commits as <a href="https://github.com/{name}">@{name}</a> in <a href="{request.form["repo"]}">{repname}</a>', form=request.form)


@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    global n
    if request.method == 'GET':
        return render_template('contribute.html', action="/contribute")
    start = 0
    for j in range(52):
        if start:
            break
        for i in range(7):
            if int(request.form[f'{i} {j}']):
                start = j
                break
    end = 0
    for j in range(51, -1, -1):
        if end:
            break
        for i in range(7):
            if int(request.form[f'{i} {j}']):
                end = j
                break
    txt = ['' for i in range(7)]
    for i in range(7):
        for j in range(start, end+1):
            if int(request.form[f'{i} {j}']):
                txt[i] += '#'
            else:
                txt[i] += ' '
    txt = "[\n\t'" + "',\n\t'".join(txt) + "'\n];"
    with open('static/script.js', 'a') as f:
        f.write(f"\ntxt['{request.form['alias']}'] = {txt}\n")
        f.write(f"pub.push('{request.form['alias']}');\n")
    if request.form['auth']:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': 'token '+request.form['auth']
        }
        response = requests.post(
            'https://api.github.com/repos/heckerfr0d/gitfitti-web/forks', headers=headers)
        print(response)
        url = "https://api.github.com/repos/"+request.form['name']+"/gitfitti-web/contents/static/script.js"
        base64content = base64.b64encode(open("static/script.js", "rb").read())
        data = requests.get(url+'?ref=main', headers=headers).json()
        sha = data['sha']
        message = json.dumps({"message": "Adding " + request.form['alias'] + " to js dict",
                              "branch": "main",
                              "content": base64content.decode("utf-8"),
                              "sha": sha
                              })
        res = requests.put(url, data=message, headers=headers)
        print(res)
        message = json.dumps({
            "title": "Expanding js dict",
            "body": "Added '" + request.form['alias'] + "' to js dict",
            "head": request.form['name'] + ":main",
            "base": "main"
        })
        print(headers)
        print(message)
        print(requests.post("https://api.github.com/repos/heckerfr0d/gitfitti-web/pulls",
              data=message, headers=headers))
    else:
        if request.form['name']:
            cont.append(request.form['name'])
        n += 1
    return render_template('contribute.html', action="/contribute", form=request.form)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global n
    if request.method == 'GET':
        return render_template('admin.html', action="/admin", n=n)
    git.cmd.Git().clone(
        f"https://{request.form['name']}:{request.form['password']}@github.com/heckerfr0d/gitfitti-web")
    repo = git.Repo.init('gitfitti-web')
    with open('static/script.js', 'rb') as fin:
        with open('gitfitti-web/static/script.js', 'wb') as fout:
            shutil.copyfileobj(fin, fout)
    repo.git.add(update=True)
    author = git.Actor(request.form['name'], request.form['email'])
    thanks = ""
    if cont:
        thanks = '@'+', @'.join(cont)
    repo.index.commit(
        f'Merging {n} public contributions\n Thanks {thanks} :heart:', author=author)
    origin = repo.remote(name='origin')
    origin.push()
    shutil.rmtree('gitfitti-web')
    n = 0
    cont.clear()
    return render_template('admin.html', action="/admin", n=n, form=request.form)


if __name__ == "__main__":
    app.run()
