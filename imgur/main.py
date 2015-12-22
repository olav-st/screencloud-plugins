import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QUrl
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QMessageBox
from PythonQt.QtUiTools import QUiLoader
import pyimgur, time, os

###############################
## This is a temporary fix, should be removed when a newer python version is used ##
import logging
logging.captureWarnings(True)
###############################

class ImgurUploader():
	def __init__(self):
		self.uil = QUiLoader()
		self.loadSettings()
		
	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_account.button_authenticate.connect("clicked()", self.startAuthenticationProcess)
		self.settingsDialog.group_account.widget_loggedIn.button_logout.connect("clicked()", self.logOut)
		self.settingsDialog.group_name.input_name.connect("textChanged(QString)", self.nameFormatEdited)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		
		self.loadSettings()
		self.settingsDialog.group_clipboard.radio_dontcopy.setChecked(not self.copyLink)
		self.settingsDialog.group_clipboard.radio_directlink.setChecked(self.copyDirectLink)
		self.updateUi()
		self.settingsDialog.open()

	def updateUi(self):
		#self.loadSettings()
		if self.access_token and self.refresh_token:
			self.settingsDialog.group_account.widget_loggedIn.show()
			self.settingsDialog.group_account.button_authenticate.hide()
			self.settingsDialog.group_account.radio_account.setChecked(True)
			self.settingsDialog.group_account.widget_loggedIn.label_user.setText(self.username)
		else:
			self.settingsDialog.group_account.widget_loggedIn.hide()
			self.settingsDialog.group_account.button_authenticate.show()
		if self.uploadAnon and self.settingsDialog.group_clipboard.radio_dontcopy.checked:
			self.settingsDialog.group_clipboard.radio_imgur.setChecked(True)
		self.settingsDialog.group_account.radio_anon.setChecked(self.uploadAnon)
		self.settingsDialog.group_name.input_name.setText(self.nameFormat)
		self.settingsDialog.adjustSize()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("imgur")
		self.uploadAnon = settings.value("anonymous", "true") in ['true', True]
		self.copyLink = settings.value("copy-link", "true") in ['true', True]
		self.copyDirectLink = settings.value("copy-direct-link", "false") in ['true', True]
		self.access_token = settings.value("access-token", "")
		self.refresh_token = settings.value("refresh-token", "")
		self.nameFormat = settings.value("name-format", "Screenshot at %H:%M:%S")
		self.username = settings.value("username", "")
		settings.endGroup()
		settings.endGroup()
		if self.uploadAnon:
			self.imgur = pyimgur.Imgur("7163c05b94dcf99")
		else:
			self.imgur = pyimgur.Imgur("7163c05b94dcf99", "5132015d173997bbb52e1d9e093d882abed8d9f1", self.access_token, self.refresh_token)

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("imgur")
		settings.setValue("anonymous", self.settingsDialog.group_account.radio_anon.checked)
		settings.setValue("copy-link", not self.settingsDialog.group_clipboard.radio_dontcopy.checked)
		settings.setValue("copy-direct-link", self.settingsDialog.group_clipboard.radio_directlink.checked)
		settings.setValue("access-token", self.access_token)
		settings.setValue("refresh-token", self.refresh_token)
		settings.setValue("name-format", self.settingsDialog.group_name.input_name.text)
		settings.setValue("username", self.username)
		settings.endGroup()
		settings.endGroup()
	
	def isConfigured(self):
		self.loadSettings()
		if self.uploadAnon:
			return True
		else:
			return self.access_token and self.refresh_token

	def getFilename(self):
		self.loadSettings()
		return ScreenCloud.formatFilename(self.nameFormat)
	      
	def upload(self, screenshot, name):
		self.loadSettings()
		#Make sure we have a up to date token
		if not self.uploadAnon:
			try:
				self.imgur.refresh_access_token()
			except Exception as e:
				ScreenCloud.setError("Failed to refresh imgur access token. " + e.message)
				return False
		#Save to a temporary file
		timestamp = time.time()
		try:
			tmpFilename = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		except AttributeError:
			from PythonQt.QtCore import QStandardPaths #fix for Qt5
			tmpFilename = QStandardPaths.writableLocation(QStandardPaths.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())
		#Upload!
		try:
			uploaded_image = self.imgur.upload_image(tmpFilename, title=ScreenCloud.formatFilename(name, False))
		except Exception as e:
			ScreenCloud.setError("Failed to upload to imgur. " + e.message)
			return False
		if self.copyLink:
			if self.copyDirectLink:
				ScreenCloud.setUrl(uploaded_image.link)
			else:
				ScreenCloud.setUrl("https://imgur.com/" + uploaded_image.id)
		return True

	def startAuthenticationProcess(self):
		self.saveSettings()
		self.loadSettings()
		auth_url = self.imgur.authorization_url('pin')
		QDesktopServices.openUrl(QUrl(auth_url))
		try:
			pin = raw_input("Enter PIN from imgur website:")
		except NameError:
			pin = input("Enter PIN from imgur website:")
		if pin:
			try:
				self.access_token, self.refresh_token = self.imgur.exchange_pin(pin)
			except KeyError as e:
				QMessageBox.critical(self.settingsDialog, "Imgur key error", "Failed to exchange pin. " + e.message)
		self.access_token, self.username = self.imgur.refresh_access_token()
		self.saveSettings()
		self.updateUi()

	def logOut(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("imgur")
		settings.remove("access-token")
		settings.remove("refresh-token")
		settings.remove("username")
		settings.setValue("anonymous", "true")
		settings.endGroup()
		settings.endGroup()
		self.loadSettings()
		self.updateUi()

	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_name.label_example.setText(ScreenCloud.formatFilename(nameFormat, False))
