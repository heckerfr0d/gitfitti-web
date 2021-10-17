from flask.helpers import url_for
import git
import datetime
import os
import shutil
import requests
import base64
import json

TOKEN = os.getenv('TOKEN')


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


def getActiveDates(dates, a):
    ad = []
    for i in range(7):
        for j in range(52):
            for k in range(a[i][j]):
                ad.append(dates[i][j])
    return ad


def commit(name, email, url, repname, a, nc, year=None):
    if year:
        dates = getActiveDates(getDates(int(year)), a)
    else:
        dates = getActiveDates(getDates(), a)
    author = git.Actor(name, email)
    if not os.path.isdir(repname):
        try:
            git.cmd.Git().clone(url)
        except:
            return -1
    rep = git.Repo.init(repname)
    for date in dates:
        for n in range(nc):
            rep.index.commit("made with love by gitfitti", author=author,
                             committer=author, author_date=date.isoformat())
    try:
        rep.remotes.origin.set_url(url)
    except:
        rep.create_remote('origin', url)
    try:
        rep.remotes.origin.push()
        shutil.rmtree(repname)
    except:
        shutil.rmtree(repname)
        return -2
    return nc*len(dates)


def editJS(alias, a):
    start = 0
    for j in range(52):
        if start:
            break
        for i in range(7):
            if a[i][j]:
                start = j
                break
    end = 0
    for j in range(51, -1, -1):
        if end:
            break
        for i in range(7):
            if a[i][j]:
                end = j
                break
    txt = ['' for i in range(7)]
    for i in range(7):
        for j in range(start, end+1):
            if a[i][j]:
                txt[i] += '#'
            else:
                txt[i] += ' '
    txt = "[\n\t'" + "',\n\t'".join(txt) + "'\n];"
    with open('static/script.js', 'a') as f:
        f.write(f"\ntxt['{alias}'] = {txt}\n\n")
        if len(alias)>1:
            f.write(f"pub.push('{alias}');\n\n")


def openPR(name, alias, auth):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token '+auth
    }
    requests.post(
        'https://api.github.com/repos/heckerfr0d/gitfitti-web/forks', headers=headers)
    url = "https://api.github.com/repos/" + \
        name+"/gitfitti-web/contents/static/script.js"
    base64content = base64.b64encode(open('static/script.js', "rb").read())
    data = requests.get(url+'?ref=main', headers=headers).json()
    sha = data['sha']
    message = json.dumps({"message": "Adding '" + alias + "' to js dict",
                          "branch": "main",
                          "content": base64content.decode("utf-8"),
                          "sha": sha
                          })
    requests.put(url, data=message, headers=headers)
    message = json.dumps({
        "title": "Expanding js dict",
        "body": "Added '" + alias + "' to js dict",
        "head": name + ":main",
        "base": "main"
    })
    PR = requests.post("https://api.github.com/repos/heckerfr0d/gitfitti-web/pulls",
                       data=message, headers=headers).json()
    return PR['html_url']


def merge(n, cont):
    git.cmd.Git().clone(
        f"https://heckerfr0d:{TOKEN}@github.com/heckerfr0d/gitfitti-web")
    repo = git.Repo.init('gitfitti-web')
    with open('static/script.js', 'rb') as fin:
        with open('gitfitti-web/static/script.js', 'wb') as fout:
            shutil.copyfileobj(fin, fout)
    repo.git.add(update=True)
    author = git.Actor('heckerfr0d', 'hadif_b190513cs@nitc.ac.in')
    thanks = ""
    if cont:
        thanks = '@'+', @'.join(cont)
    repo.index.commit(
        f'Merging {n} public contributions\n Thanks {thanks} :heart:', author=author)
    origin = repo.remote(name='origin')
    origin.push()
    shutil.rmtree('gitfitti-web')
    return thanks

