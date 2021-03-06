from . import celery
import git
import datetime
import os
import shutil
import requests
import base64
import json


def getDates(year=None):
    if year:
        jan1 = datetime.datetime(year=year, month=1, day=1, hour=10, minute=20, second=59)
    else:
        jan1 = datetime.datetime.today() - datetime.timedelta(weeks=53)

    jan1 = jan1.replace(microsecond=0)

    first_sunday = jan1 + datetime.timedelta(days=(6-jan1.weekday()) % 7)
    dates = [list() for x in range(7)]
    for x in range(52 * 7):
        dates[x % 7].append(first_sunday + datetime.timedelta(x))
    return dates


def getActiveDates(a, nc, year=None):
    ad = []
    if year:
        dates = getDates(int(year))
    else:
        dates = getDates()
    for j in range(52):
        for i in range(7):
            ad += [dates[i][j].isoformat()]*(a[i][j]*int(nc))
    return ad



@celery.task(bind=True)
def commit(self, name, email, auth, url, repname, dates, deleterep=False):
    author = git.Actor(name, email)
    total = len(dates)
    i = 0
    os.mkdir(name)
    branch = 'main'
    try:
        self.update_state(state='PROGRESS',
                          meta={'current': i,
                                'total': total,
                                'status': 'Looking for your repo...'})
        headers = {
            'Authorization': 'token '+auth
        }
        api = f'https://api.github.com/repos/{name}/{repname}'
        private = True
        resp = requests.get(api, headers=headers)
        if resp.status_code == 200:
            self.update_state(state='PROGRESS',
                                meta={'current': i,
                                        'total': total,
                                        'status': 'Found it! Cloning...'})
            data = resp.json()
            branch = data['default_branch']
            git.cmd.Git(name).clone(url)
            if deleterep:
                self.update_state(state='PROGRESS',
                                    meta={'current': i,
                                            'total': total,
                                            'status': 'Recreating your repo...'})
                private = data['private']
                shutil.rmtree(os.path.join(name, repname, '.git'))
                requests.delete(api, headers=headers)
                data = json.dumps({"name": repname, "description": "A repo for GitHub graffiti", "private": private})
                requests.post('https://api.github.com/user/repos', headers=headers, data=data)
        else:
            self.update_state(state='PROGRESS',
                                meta={'current': i,
                                        'total': total,
                                        'status': 'Creating the repo...'})
            data = json.dumps({"name": repname, "description": "A repo for GitHub graffiti", "private": private})
            requests.post('https://api.github.com/user/repos', headers=headers, data=data)
            git.cmd.Git(name).clone(url)
    except:
        shutil.rmtree(name)
        return {'current': i, 'total': total, 'status': "Creation or cloning failed!",
        'result': -1}

    rep = git.Repo.init(os.path.join(name, repname))
    rep.git.add(all=True)
    for date in dates:
        self.update_state(state='PROGRESS',
                          meta={'current': i,
                                'total': total,
                                'status': 'Committing...'})
        rep.index.commit("made with love by gitfitti", author=author,
                            committer=author, commit_date=date, author_date=date)
        i += 1
    self.update_state(state='PROGRESS',
                          meta={'current': i,
                                'total': total,
                                'status': 'Pushing...'})
    rep.active_branch.rename(branch)
    try:
        rep.remotes.origin.set_url(url)
    except:
        rep.create_remote('origin', url)
    try:
        rep.remotes.origin.push(refspec=f"{branch}:{branch}", force=True)
        shutil.rmtree(name)
    except:
        shutil.rmtree(name)
        return {'current': i, 'total': total, 'status': "Push Failed!",
            'result': -2}
    return {'current': i, 'total': total, 'status': 'All done!',
            'result': i}


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
    with open('gitfitti/static/script.js', 'a') as f:
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
        name+"/gitfitti-web/contents/gitfitti/static/script.js"
    base64content = base64.b64encode(open('gitfitti/static/script.js', "rb").read())
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

