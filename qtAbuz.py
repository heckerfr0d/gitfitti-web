import sys, datetime, os, git
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QWidget, QLineEdit, QPushButton, QCheckBox, QGridLayout, QComboBox, QVBoxLayout
from PyQt6.QtGui import QIcon

def getDates(year):
    jan1 = datetime.datetime(year, 1, 1, 4, 20, 59)
    onDay = lambda date, day: date + datetime.timedelta(days=(day-date.weekday())%7)
    first_sunday = onDay(jan1, 6)
    dates = [list() for x in range(7)]
    # list of weekdays
    for x in range(52 * 7):
        dates[x % 7].append(first_sunday + datetime.timedelta(x))
    return dates

class App(QWidget):
    def __init__(self):
        global y, checkM, name, email, repo
        super().__init__()
        self.setWindowTitle('GitHub Abuz!')
        self.setWindowIcon(QIcon('icon.png'))
        layout = QGridLayout()
        vl = QVBoxLayout()
        hl = QHBoxLayout()
        y = QComboBox()
        name = QLineEdit()
        email = QLineEdit()
        repo = QLineEdit()
        self.setLayout(vl)
        y.addItem('Select year...')
        for yr in range(2021, 2000, -1):
            y.addItem(str(yr))
        name.setPlaceholderText('Committer name*')
        email.setPlaceholderText('Committer email*')
        repo.setPlaceholderText('repo url as https://username:password@github.com/username/reponame')
        hl.addWidget(name)
        hl.addWidget(email)
        hl.addWidget(y)
        vl.addLayout(hl)
        vl.addWidget(repo)
        vl.addLayout(layout)
        checkM = [list() for i in range(7)]
        for i in range(7):
            for j in range(51):
                m = QCheckBox()
                layout.addWidget(m, i, j)
                checkM[i].append(m)
        leggo = QPushButton('Lessgoo')
        leggo.clicked.connect(self.doit)
        vl.addWidget(leggo)
    def getActiveDates(self, dates):
        ad = []
        for i in range(7):
            for j in range(51):
                if checkM[i][j].isChecked():
                    ad.append(dates[i][j])
        return ad

    def doit(self):
        year = int(y.currentText())
        dates = self.getActiveDates(getDates(year))
        author = git.Actor(name.text(), email.text())
        repurl = repo.text()
        repname = repurl.split('/')[-1]
        git.cmd.Git().clone(repurl)
        rep = git.Repo.init(repname)
        for date in dates:
            filename = date.strftime('%Y-%m-%d-%H-%M-%S')
            filepath = os.path.join(repname, filename)
            with open(filepath, 'w') as f:
                f.write(filename)
            rep.index.add([filename])
            rep.index.commit("GitHub abuz add", author=author, committer=author, author_date=date.isoformat())
            rep.index.remove([filename])
            rep.index.commit("GitHub abuz remove", author=author, committer=author, author_date=(date+datetime.timedelta(minutes=1)).isoformat())
            os.remove(os.path.join(repname, filename))
            os.removedirs(repname)
        try:
            rep.remotes.origin.set_url(repurl)
        except:
            rep.create_remote('origin', repurl)
        rep.remotes.origin.push()
        result = QMessageBox()
        text = f"Created {len(dates)*2} commits as {name.text()} <{email.text()}> in {repname} : https://{repurl[repurl.find('github.com'):]}"
        result.setWindowIcon(QIcon('icon.png'))
        result.setWindowTitle('All Done!')
        result.setText(text)
        result.exec()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = App()
    app.setStyleSheet('''
        QLineEdit{
            color: #8b949e;
            border: 1px #30363d;
            border-radius: 3px;
        }
        QWidget{
            background-color: #0d1117;
        }
        QCheckBox {
            spacing: 0px;
            padding: 0px;
        }

        QCheckBox::indicator {
            width: 11px;
            height: 11px;
            outline: 1px solid  hsla(0, 0, 100, 0.05);
            border-radius: 3px;
        }

        QCheckBox::indicator:pressed {
            outline: 0px;
        }

        QCheckBox::indicator:unchecked {
            background-color: #161b22;
            opacity: 0.5;
        }

        QCheckBox::indicator:unchecked:hover {
            background-color: #003820;
            opacity: 1;
        }

        QCheckBox::indicator:checked {
            background-color: #10983d;
        }

        QCheckBox::indicator:checked:hover {
            background-color: #00602d;
        }


        QComboBox {
            border: 1px #30363d;
            border-radius: 3px;
            padding: 1px 18px 1px 3px;
            min-width: 6em;
            background: #1c2128;
            color: #f0f6fc;
        }

        QComboBox:editable {
            background: #1c2128;
            color: #f0f6fc;
        }

        QComboBox:!editable, QComboBox::drop-down:editable {
            background: #1c2128;
            color: #f0f6fc;
        }

        /* QComboBox gets the "on" state when the popup is open */
        QComboBox:!editable:on, QComboBox::drop-down:editable:on {
            background: #1c2128;
            color: #f0f6fc;
        }

        QComboBox:hover {
            background: #30363d;
        }

        QComboBox:on { /* shift the text when the popup opens */
            padding-top: 3px;
            padding-left: 4px;
            color: #f0f6fc;
        }

        QComboBox::drop-down {
            border: 1px solid #30363d;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            background-color: #0d1117;
            color: #f0f6fc;
        }


        QComboBox::down-arrow:on { /* shift the arrow when popup is open */
            top: 1px;
            left: 1px;
            color: #f0f6fc;
        }

        QComboBox QAbstractItemView {
            border: 1px solid #30363d;
            selection-background-color: #0d1117;
            color: #f0f6fc;
        }
        QLabel{
            color: #f0f6fc;
        }
        QPushButton {
            border: 1px solid #30363d;
            border-radius: 4px;
            background-color: #161b22;
            color: #58a6ff;
            min-width: 80px;
        }

        QPushButton:pressed {
            background-color: #0d1117;
            border: 0px;
        }

        QPushButton:hover {
            background-color: #30363d;
        }

        QPushButton:flat {
            border: none; /* no border for a flat push button */
        }



        QScrollBar:vertical
        {
            background-color: #161b22;
            width: 15px;
            margin: 15px 3px 15px 3px;
            border: 1px transparent #2A2929;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical
        {
            background-color: #58a6ff;
            min-height: 5px;
            border-radius: 4px;
        }

        QScrollBar::sub-line:vertical
        {
            margin: 3px 0px 3px 0px;
            border: 0px;
            height: 10px;
            width: 10px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }

        QScrollBar::add-line:vertical
        {
            margin: 3px 0px 3px 0px;
            border: 0px;
            height: 10px;
            width: 10px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }

        QScrollBar::sub-line:vertical:hover,QScrollBar::sub-line:vertical:on
        {

            border: 0px;
            height: 10px;
            width: 10px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }


        QScrollBar::add-line:vertical:hover, QScrollBar::add-line:vertical:on
        {
            border: 0px;
            height: 10px;
            width: 10px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }

        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical
        {
            background: none;
        }


        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
        {
            background: none;
        }

    ''')
    w.show()
    sys.exit(app.exec())
