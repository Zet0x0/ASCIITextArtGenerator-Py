# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QColorDialog, QMenu, QFontDialog, QMessageBox,
                             QFileDialog, QLabel, QVBoxLayout, QPlainTextEdit,
                             QPushButton, QApplication, QDialog)
from PyQt6.QtGui import (QKeySequence, QFont, QImage, QColor, QPainter,
                         QAction, QPixmap, QImageWriter, QShortcut)
from PyQt6.QtCore import QThread, Qt, pyqtSignal, QPoint, QFile
from typing import Callable


class ProcessingThread(QThread):
    __slots__ = (
        "asciiCharacters",
        "image",
    )
    onResultReady = pyqtSignal(str)

    def __init__(self, onResultReady: Callable) -> None:
        super().__init__()

        self.asciiCharacters, self.image = [
            "@", "#", "$", "%", "?", "*", "+", ";", ":", ",", " "
        ], None
        self.onResultReady.connect(onResultReady)

    def start(self, image: QImage) -> None:
        self.image = image
        super().start()

    def run(self) -> None:
        self.onResultReady.emit("".join(
            w.rstrip() + "\n" for w in ("".join(
                self.asciiCharacters[self.image.pixelColor(x, y).value() // 25]
                for x in range(self.image.width()))
                                        for y in range(self.image.height()))
            if w.strip()))


class MainWindow(QDialog):
    __slots__ = (
        "background",
        "foreground",
    )

    def __init__(self) -> None:
        super().__init__()

        def changeColor(forBackground: bool = False) -> None:
            color = QColorDialog.getColor(
                (self.background if forBackground else self.foreground),
                title=
                f"Select {'Background' if forBackground else 'Foreground'}",
                options=QColorDialog.ColorDialogOption.ShowAlphaChannel)
            if not color.isValid(): return

            (
                backgroundColorPicker
                if forBackground else foregroundColorPicker
            ).setStyleSheet(
                f"QLabel {{ color: transparent; background-color: rgba{color.getRgb()}; }}"
            )

            if forBackground: self.background = color
            else: self.foreground = color

            generatedTextWindow.setStyleSheet(
                f"QPlainTextEdit {{ background-color: rgba{self.background.getRgb()}; color: rgba{self.foreground.getRgb()}; border: none; }}"
            )

        def resultReady(result: str) -> None:
            (generatedTextWindow.show if generatedTextWindow.isHidden() else
             generatedTextWindow.activateWindow)()
            generatedTextWindow.setPlainText(result)
            self.setDisabled(False)

        def changeFont() -> None:
            font = QFontDialog.getFont(changeFontButton.font())
            if not font[1]: return

            changeFontButton.setFont(font[0])
            self.setFixedSize(self.sizeHint())

        def process() -> None:
            if not textBox.toPlainText().strip(): return

            self.setDisabled(True)

            pixmap = QPixmap(changeFontButton.fontMetrics().size(
                0, textBox.toPlainText()))
            painter = QPainter(pixmap)

            painter.setFont(changeFontButton.font())
            painter.fillRect(pixmap.rect(), Qt.GlobalColor.white)
            painter.drawText(pixmap.rect(), 0, textBox.toPlainText())

            painter.end()

            processingThread.start(
                QImage(
                    pixmap.scaledToWidth(
                        pixmap.width() * 2,
                        Qt.TransformationMode.SmoothTransformation)))

        layout, textBox, processButton = QVBoxLayout(self), QPlainTextEdit(
            "Hello World!",
            toolTip="Text goes here",
            textChanged=lambda: processButton.setDisabled(
                not textBox.toPlainText().strip())), QPushButton(
                    "Process", clicked=process)
        self.backgroundColor, self.foregroundColor, processingThread = QColor(
            255, 255, 255), QColor(0, 0, 0), ProcessingThread(resultReady)
        backgroundColorPicker, foregroundColorPicker, changeFontButton = QLabel(
            toolTip="Background color",
            frameShape=QLabel.Shape.StyledPanel,
            styleSheet=
            "QLabel { color: transparent; background-color: #FFFFFF; }"
        ), QLabel(toolTip="Text color",
                  frameShape=QLabel.Shape.StyledPanel,
                  styleSheet=
                  "QLabel { color: transparent; background-color: #000000; }"
                  ), QPushButton("Change font",
                                 clicked=changeFont,
                                 toolTip="Change font",
                                 font=QFont("Arial Black", 12))

        backgroundColorPicker.mousePressEvent, foregroundColorPicker.mousePressEvent = lambda event: changeColor(
            True), lambda event: changeColor()

        layout.addWidget(textBox)
        layout.addWidget(changeFontButton)
        layout.addWidget(backgroundColorPicker)
        layout.addWidget(foregroundColorPicker)
        layout.addWidget(processButton)

        self.setFixedSize(self.sizeHint())
        self.show()


def contextMenuRequested(pos: QPoint) -> None:
    menu = QMenu()

    saveAction, toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction = QAction(
        "Save As",
        shortcut=QKeySequence(QKeySequence.StandardKey.Save)), QAction(
            "Hide or show vertical scroll bar"), QAction(
                "Hide or show horizontal scroll bar")

    menu.addAction(saveAction)
    menu.addSeparator()
    menu.addActions(
        [toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction])

    action = menu.exec(generatedTextWindow.mapToGlobal(pos))
    if not action: return

    if action in {
            toggleVerticalScrollBarAction, toggleHorizontalScrollBarAction
    }:
        return (
            generatedTextWindow.setVerticalScrollBarPolicy
            if action == toggleVerticalScrollBarAction else
            generatedTextWindow.setHorizontalScrollBarPolicy
        )(Qt.ScrollBarPolicy.ScrollBarAsNeeded if (
            generatedTextWindow.verticalScrollBarPolicy if action ==
            toggleVerticalScrollBarAction else generatedTextWindow.
            horizontalScrollBarPolicy)() == Qt.ScrollBarPolicy.
          ScrollBarAlwaysOff else Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    saveGeneratedText()


def saveGeneratedText() -> None:
    file = QFileDialog.getSaveFileName(
        filter=
        f"Plain Text File (*.txt);; Image File ({'; '.join(f'*.{x.data().decode()}' for x in QImageWriter.supportedImageFormats())})"
    )
    if not file[0]: return

    if file[1].startswith("Plain "):
        file = QFile(file[0])

        if not file.open(QFile.OpenModeFlag.WriteOnly):
            return QMessageBox.critical(
                generatedTextWindow, "Error",
                f"Could not open the file: [{file.error()}] {file.errorString()}"
            )

        file.write(generatedTextWindow.toPlainText().encode("UTF-8"))

        if file.error() != QFile.FileError.NoError:
            QMessageBox.critical(
                generatedTextWindow, "Error",
                f"Could not write to file: [{file.error()}] {file.errorString()}"
            )
        else:
            file.close()
            QMessageBox.information(
                generatedTextWindow, "Success",
                f"Successfully saved to {file.fileName()}")

        return

    pixmap = QPixmap(generatedTextWindow.fontMetrics().size(
        0, generatedTextWindow.toPlainText()))
    painter = QPainter(pixmap)

    painter.fillRect(pixmap.rect(), mainWindow.background)
    painter.setFont(generatedTextWindow.font())
    painter.setPen(mainWindow.foreground)

    painter.drawText(pixmap.rect(), 0, generatedTextWindow.toPlainText())

    painter.end()

    if not pixmap.save(file[0], quality=100):
        return QMessageBox.critical(generatedTextWindow, "Error",
                                    f"Could not save to {file[0]}")

    QMessageBox.information(generatedTextWindow, "Success",
                            f"Successfully saved to {file[0]}")


app = QApplication([], applicationName="ASCII Text Art Generator")

mainWindow, generatedTextWindow = MainWindow(), QPlainTextEdit(
    windowTitle="Generated ASCII Text Art",
    readOnly=True,
    lineWrapMode=QPlainTextEdit.LineWrapMode.NoWrap,
    font=QFont("Consolas", 12),
    styleSheet="QPlainTextEdit { border: none; }",
    contextMenuPolicy=Qt.ContextMenuPolicy.CustomContextMenu,
    customContextMenuRequested=contextMenuRequested)
QShortcut(QKeySequence(QKeySequence.StandardKey.Save), generatedTextWindow,
          saveGeneratedText)

app.exec()