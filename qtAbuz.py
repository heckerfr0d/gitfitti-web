import sys
import datetime
import os
import git
from font import Font
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QSpinBox, QWidget, QLineEdit, QPushButton, QCheckBox, QGridLayout, QComboBox, QVBoxLayout
from PyQt6.QtGui import QIcon


def getDates(year=None):
    if year:
        jan1 = datetime.datetime(year=year, month=1, day=1, hour=10, minute=20, second=59)
    else:
        jan1 = datetime.datetime.now() - datetime.timedelta(weeks=53)
        jan1 -= datetime.timedelta(microseconds=jan1.microsecond)
    def onDay(date, day): return date + datetime.timedelta(days=(day-date.weekday()) % 7)
    first_sunday = onDay(jan1, 6)
    dates = [list() for x in range(7)]
    for x in range(52 * 7):
        dates[x % 7].append(first_sunday + datetime.timedelta(x))
    return dates

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('GitHub Abuz!')
        self.setWindowIcon(QIcon('icon.png'))
        layout = QGridLayout()
        vl = QVBoxLayout()
        hl = QHBoxLayout()
        hl2 = QHBoxLayout()
        hl3 = QHBoxLayout()
        self.y = QComboBox()
        self.name = QLineEdit()
        self.email = QLineEdit()
        self.passw = QLineEdit()
        self.repo = QLineEdit()
        self.type = QLineEdit()
        self.fonts = QComboBox()
        self.err = QMessageBox()
        self.nc = QSpinBox()
        lbl = QLabel('Commits/day:')
        prev = QPushButton('Translate')
        invert = QPushButton('Invert')
        leggo = QPushButton('Do it')
        invert.clicked.connect(self.invert)
        leggo.clicked.connect(self.doit)
        prev.clicked.connect(self.textCheck)
        self.name.textChanged[str].connect(self.rmph)
        self.email.textChanged[str].connect(self.rmph)
        self.passw.textChanged[str].connect(self.rmph)
        self.type.textChanged[str].connect(self.rmph)
        self.repo.textChanged[str].connect(self.rmph)
        self.y.addItem('Year (default: last 52 weeks)')
        for yr in range(datetime.datetime.now().year+5, datetime.datetime.now().year-20, -1):
            self.y.addItem(str(yr))
        self.fonts.addItems(os.listdir('Fonts'))
        self.name.setPlaceholderText('Committer name')
        self.email.setPlaceholderText('Committer email')
        self.passw.setPlaceholderText('Password')
        self.passw.setEchoMode(QLineEdit.EchoMode.Password)
        self.repo.setPlaceholderText('Link to repo')
        self.type.setPlaceholderText('Translate text to tile art!')
        self.nc.setMinimum(1)
        self.nc.setValue(1)
        self.err.setWindowIcon(QIcon('icon.png'))
        self.err.setWindowTitle('Error!')
        hl.addWidget(self.name)
        hl.addWidget(self.email)
        hl.addWidget(self.passw)
        hl3.addWidget(self.repo)
        hl3.addWidget(self.y)
        hl3.addWidget(lbl)
        hl3.addWidget(self.nc)
        hl2.addWidget(self.type)
        hl2.addWidget(self.fonts)
        hl2.addWidget(prev)
        hl2.addWidget(invert)
        vl.addLayout(hl)
        vl.addLayout(hl3)
        vl.addLayout(layout)
        vl.addLayout(hl2)
        vl.addWidget(leggo)
        self.setLayout(vl)
        self.checkM = [list() for i in range(7)]
        for i in range(7):
            for j in range(52):
                m = QCheckBox()
                layout.addWidget(m, i, j)
                self.checkM[i].append(m)
    def rmph(self):
        self.setStyleSheet('''
        QLineEdit[text=""]{
            border: 1px #30363d;
            border-radius: 3px;
            padding: 1px 18px 1px 3px;
            background-color: #1c2128;
            color: #8b949e;
        }
        QLineEdit{
            border: 1px #30363d;
            border-radius: 3px;
            padding: 1px 18px 1px 3px;
            background-color: #1c2128;
            color: #f0f6fc;
        }
        QLineEdit:hover {
            border: 0.5px solid #c9d1d9;
        }
        QLineEdit:focus {
            border: 1px solid #c9d1d9;
        }''')
    def getActiveDates(self, dates):
        ad = []
        for i in range(7):
            for j in range(52):
                if self.checkM[i][j].isChecked():
                    ad.append(dates[i][j])
        return ad

    def doit(self):
        try:
            year = int(self.y.currentText())
            dates = self.getActiveDates(getDates(year))
        except:
            dates = self.getActiveDates(getDates())
        author = git.Actor(self.name.text(), self.email.text())
        if not self.name.text() or not self.email.text():
            self.err.setText('Did you enter your name and email? 🙄')
            self.err.exec()
            return

        repurl = "https://" + self.name.text() + ":" + self.passw.text() + "@" + self.repo.text()[8:]
        repname = repurl.split('/')[-1].split('.')[0]
        if not os.path.isdir(repname):
            try:
                git.cmd.Git().clone(repurl)
            except:
                self.err.setText('Could not clone the repo. Ensure that the remote repo exists and that you have access to it.')
                self.err.exec()
                return
        rep = git.Repo.init(repname)
        for date in dates:
            for n in range(self.nc.value()):
                rep.index.commit("committed for the lullzz!!", author=author, committer=author, author_date=date.isoformat())
        try:
            rep.remotes.origin.set_url(repurl)
        except:
            rep.create_remote('origin', repurl)
        try:
            rep.remotes.origin.push()
        except:
            self.err.setText('Error pushing. Verify you have permissions to push to the repo and that the given credentials are correct')
            self.err.exec()
            return
        result = QMessageBox()
        text = f"Created {len(dates)*2} commits as {self.name.text()} <{self.email.text()}> in {repname} : {self.repo.text()}"
        result.setWindowIcon(QIcon('icon.png'))
        result.setWindowTitle('All Done!')
        result.setText(text)
        result.exec()
        os.remove(repname)

    def textCheck(self):
        for r in self.checkM:
            for m in r:
                m.setChecked(False)
        text_to_render = self.type.text()
        font = Font(os.path.join('Fonts', self.fonts.currentText()), 8)
        try:
            text = repr(font.render_text(text_to_render, 52, 7))
            text_by_weekday = text.split('\n')
            for i in range(7):
                for j in range(51):
                    if text_by_weekday[i][j] == '#':
                        self.checkM[i][j].setChecked(True)
        except:
            self.err.setText('You typed too long :(')
            self.err.exec()

    def invert(self):
        for r in self.checkM:
            for m in r:
                if m.isChecked():
                    m.setChecked(False)
                else:
                    m.setChecked(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = App()
    app.setStyleSheet('''
        QLineEdit[text=""]{
            border: 1px #30363d;
            border-radius: 3px;
            padding: 1px 18px 1px 3px;
            background-color: #1c2128;
            color: #8b949e;
        }
        QLineEdit{
            color: #f0f6fc;
        }
        QLineEdit:hover {
            border: 0.5px solid #c9d1d9;
        }
        QLineEdit:focus {
            border: 1px solid #c9d1d9;
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
        QSpinBox {
            padding-right: 15px; /* make room for the arrows */
            border: 1px solid #30363d;
            border-radius: 3px;
            color: #f0f6fc;
            background: solid #1c2128
        }
        QSpinBox:hover {
            border: 0.5px solid #c9d1d9;
        }
        QSpinBox:focus {
            border: 1px solid #c9d1d9;
        }
        
        QSpinBox::up-button {
            subcontrol-origin: border;
            subcontrol-position: top right; /* position at the top right corner */
            width: 14px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
            border: 1px solid #30363d;
            border-bottom: 0px;
            background: solid #30363d;
        }
        
        QSpinBox::up-arrow {
            width: 7px;
            height: 7px;
            background: solid black;
        }
        
        QSpinBox::down-button {
            subcontrol-origin: border;
            subcontrol-position: bottom right; /* position at bottom right corner */
            width: 14px;
            border: 1px solid #30363d;
            border-top: 0px;
            background: solid #30363d;
        }
        QSpinBox::down-button:hover {
        border: 0.5px solid #c9d1d9;
        }
        QSpinBox::down-button:focus {
        border: 1px solid #c9d1d9;
        border-top: 0px;
        }
        QSpinBox::up-button:hover {
        border: 0.5px solid #c9d1d9;
        }
        QSpinBox::up-button:focus {
        border: 1px solid #c9d1d9;
        border-bottom: 0px;
        }
        QSpinBox::down-arrow {
            width: 7px;
            height: 7px;
            background: solid black;
        }
    ''')
    w.show()
    sys.exit(app.exec())
