# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(502, 151)
        self.gridLayoutWidget = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 10, 132, 132))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.albumImg = QtWidgets.QLabel(self.gridLayoutWidget)
        self.albumImg.setObjectName("albumImg")
        self.gridLayout.addWidget(self.albumImg, 0, 0, 1, 1)
        self.gridLayoutWidget_3 = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget_3.setGeometry(QtCore.QRect(150, 40, 341, 21))
        self.gridLayoutWidget_3.setObjectName("gridLayoutWidget_3")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.gridLayoutWidget_3)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.songInfo = QtWidgets.QLabel(self.gridLayoutWidget_3)
        self.songInfo.setObjectName("songInfo")
        self.gridLayout_3.addWidget(self.songInfo, 0, 0, 1, 1)
        self.gridLayoutWidget_2 = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(150, 10, 341, 21))
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.songTitle = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.songTitle.setObjectName("songTitle")
        self.gridLayout_2.addWidget(self.songTitle, 0, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(150, 110, 51, 31))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_3 = QtWidgets.QPushButton(Dialog)
        self.pushButton_3.setGeometry(QtCore.QRect(420, 110, 71, 31))
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(210, 110, 51, 31))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_4 = QtWidgets.QPushButton(Dialog)
        self.pushButton_4.setGeometry(QtCore.QRect(270, 110, 51, 31))
        self.pushButton_4.setObjectName("pushButton_4")
        self.gridLayoutWidget_4 = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget_4.setGeometry(QtCore.QRect(150, 70, 51, 21))
        self.gridLayoutWidget_4.setObjectName("gridLayoutWidget_4")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.gridLayoutWidget_4)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.staticLabel_1 = QtWidgets.QLabel(self.gridLayoutWidget_4)
        self.staticLabel_1.setObjectName("staticLabel_1")
        self.gridLayout_4.addWidget(self.staticLabel_1, 0, 0, 1, 1)
        self.gridLayoutWidget_5 = QtWidgets.QWidget(Dialog)
        self.gridLayoutWidget_5.setGeometry(QtCore.QRect(210, 70, 49, 21))
        self.gridLayoutWidget_5.setObjectName("gridLayoutWidget_5")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.gridLayoutWidget_5)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.favOrNot = QtWidgets.QLabel(self.gridLayoutWidget_5)
        self.favOrNot.setObjectName("favOrNot")
        self.gridLayout_5.addWidget(self.favOrNot, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Pyxis"))
        self.albumImg.setText(_translate("Dialog", "albumImg"))
        self.songInfo.setText(_translate("Dialog", "songInfo"))
        self.songTitle.setText(_translate("Dialog", "songTitle"))
        self.pushButton.setText(_translate("Dialog", "Start"))
        self.pushButton_3.setText(_translate("Dialog", "Like"))
        self.pushButton_2.setText(_translate("Dialog", "Pause"))
        self.pushButton_4.setText(_translate("Dialog", "Skip"))
        self.staticLabel_1.setText(_translate("Dialog", "Favorite:"))
        self.favOrNot.setText(_translate("Dialog", "-"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
