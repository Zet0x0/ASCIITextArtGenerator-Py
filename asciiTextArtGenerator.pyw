# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QColorDialog, QFrame, QLabel, QGridLayout,
                             QComboBox, QLineEdit, QSpinBox, QPlainTextEdit,
                             QPushButton, QApplication, QDialog, QTextEdit)
from PyQt6.QtCore import QThread, pyqtSignal, QSize, Qt
from PIL import Image, ImageDraw, ImageFont
from numpy import uint8, array
from PyQt6.QtGui import QFont


class TextThread(QThread):
    __slots__ = (
        "fontSize",
        "text",
        "char",
    )
    onReady = pyqtSignal(str)

    def __init__(self, onReady: "function",
                 setDisabledFunction: "function") -> None:
        super().__init__(started=lambda: setDisabledFunction(True),
                         finished=lambda: setDisabledFunction(False))
        self.fontSize, self.text, self.char = 12, "Hello World!", "#"
        self.onReady.connect(onReady)

    def start(self, fontSize: int, text: str, char: str) -> None:
        self.fontSize, self.text, self.char = fontSize, text, char
        super().start()

    def run(self) -> None:
        font = ImageFont.truetype("verdanab.ttf", self.fontSize)
        img = Image.new("1", font.getsize(self.text), "black")
        ImageDraw.Draw(img).text((0, 0), self.text, "white", font=font)

        chars = array([" ", self.char], dtype="U1")[array(img, dtype=uint8)]
        self.onReady.emit("\n".join(
            x for x in chars.view("U" + str(chars.shape[1])).flatten()
            if x.strip()))


class Main(QDialog):
    __slots__ = ("textThread", )

    def __init__(self) -> None:
        super().__init__()

        def mousePressEvent(background_: bool = False) -> None:
            color = QColorDialog.getColor(
                options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
            if not color.isValid(): return

            (background if background_ else foreground).setStyleSheet(
                "QLabel { color: transparent; background-color: rgba%s; }" %
                str(color.getRgb()))
            (background if background_ else foreground).setText(
                str(color.getRgb()).strip("(").strip(",)"))

        def onReady(result: str) -> None:
            textWindow.setPlainText(result)
            textWindow.setAlignment(
                getattr(Qt.AlignmentFlag, f"Align{alignment1.currentText()}")
                | getattr(Qt.AlignmentFlag, f"Align{alignment2.currentText()}")
            )

            if background.text().strip() and foreground.text().strip():
                textWindow.setStyleSheet(
                    "QTextEdit { background-color: rgba(%s); color: rgba(%s); border: none; }"
                    % (
                        background.text().strip(),
                        foreground.text().strip(),
                    ))
            elif background.text().strip():
                textWindow.setStyleSheet(
                    "QTextEdit { background-color: rgba(%s); border: none; }" %
                    background.text().strip())
            elif foreground.text().strip():
                textWindow.setStyleSheet(
                    "QTextEdit { color: rgba(%s); border: none; }" %
                    foreground.text().strip())

            (textWindow.show
             if textWindow.isHidden() else textWindow.activateWindow)()

        layout, plainText, char = QGridLayout(self), QPlainTextEdit(
            "Hello World!",
            toolTip="Text goes here",
            textChanged=lambda: processButton.setDisabled(
                not plainText.toPlainText().strip())), QLineEdit(
                    "#",
                    placeholderText="Character to use",
                    toolTip="Character to use",
                    maxLength=1)
        alignment1, alignment2, fontSize = QComboBox(
            toolTip="First alignment"), QComboBox(
                toolTip="Second alignment"), QSpinBox(toolTip="Font size")
        background, foreground, processButton = QLabel(
            toolTip="Background color",
            frameShape=QFrame.Shape.StyledPanel,
            maximumSize=QSize(20, 20),
            minimumSize=QSize(20, 20),
            styleSheet="QLabel { color: transparent; }"), QLabel(
                toolTip="Text color",
                frameShape=QFrame.Shape.StyledPanel,
                maximumSize=QSize(20, 20),
                minimumSize=QSize(20, 20),
                styleSheet="QLabel { color: transparent; }"), QPushButton(
                    "Process",
                    clicked=lambda: self.textThread.start(
                        int(fontSize.text()),
                        plainText.toPlainText().strip(),
                        char.text().strip()))
        self.textThread = TextThread(onReady, processButton.setDisabled)

        alignment1.addItems([
            "Center", "Absolute", "Baseline", "Bottom", "HCenter", "Justify",
            "Leading", "Left", "Right", "Top", "Trailing", "VCenter"
        ])
        alignment2.addItems([
            "Center", "Absolute", "Baseline", "Bottom", "HCenter", "Justify",
            "Leading", "Left", "Right", "Top", "Trailing", "VCenter"
        ])
        background.mousePressEvent, foreground.mousePressEvent = lambda event: mousePressEvent(
            True), lambda event: mousePressEvent()
        alignment1.setCurrentIndex(1)
        alignment2.setCurrentIndex(1)
        fontSize.setRange(12, 128)

        layout.addWidget(plainText, 0, 0, 1, 3)
        layout.addWidget(alignment1, 1, 0)
        layout.addWidget(alignment2, 2, 0)
        layout.addWidget(fontSize, 1, 1)
        layout.addWidget(char, 2, 1)
        layout.addWidget(background, 1, 2)
        layout.addWidget(foreground, 2, 2)
        layout.addWidget(processButton, 3, 0, 1, 3)

        self.setFixedSize(280, 300)


app = QApplication([], applicationName="ASCII Text Art Generator")
main, textWindow = Main(), QTextEdit(
    windowTitle="Generated ASCII Text Art",
    readOnly=True,
    lineWrapMode=QTextEdit.LineWrapMode.NoWrap,
    font=QFont("Consolas"),
    styleSheet="QTextEdit { border: none; }")
main.show()
app.exec()