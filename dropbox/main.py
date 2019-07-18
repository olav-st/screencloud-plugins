import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QUrl, QDir
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QMessageBox
from PythonQt.QtUiTools import QUiLoader
import time, os, sys

###############################
## This is a temporary fix, should be removed when a newer python version is used ##
import logging
logging.captureWarnings(True)
###############################

###############################
## Another temporary fix to make sure external typing.py is used with python 2 only ##
if sys.version_info < (3, 0):
	sys.path.append(ScreenCloud.getPluginDir() + chr(QDir.separator()).join(["", "dropbox", "modules", "py2typing"]))
###############################

#After sys.path modification
import dropbox

class DropboxUploader():
	def __init__(self):
		self.uil = QUiLoader()
		self.loadSettings()
		if self.access_token:
			self.client = dropbox.Dropbox(self.access_token)
		
	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_account.widget_authorize.button_authenticate.connect("clicked()", self.startAuthenticationProcess)
		self.settingsDialog.group_account.widget_loggedIn.button_logout.connect("clicked()", self.logout)
		self.settingsDialog.group_name.input_nameFormat.connect("textChanged(QString)", self.nameFormatEdited)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.loadSettings()
		self.updateUi()
		self.settingsDialog.open()

	def updateUi(self):
		self.loadSettings()
		if not self.access_token:
			self.settingsDialog.group_account.widget_loggedIn.setVisible(False)
			self.settingsDialog.group_account.widget_authorize.setVisible(True)
			self.settingsDialog.group_account.widget_authorize.button_authenticate.setEnabled(True)
			self.settingsDialog.group_name.setEnabled(False)
			self.settingsDialog.group_clipboard.setEnabled(False)
		else:
			self.settingsDialog.group_account.widget_loggedIn.setVisible(True)
			self.settingsDialog.group_account.widget_authorize.setVisible(False)
			self.settingsDialog.group_account.widget_loggedIn.label_user.setText(self.display_name)
			self.settingsDialog.group_name.setEnabled(True)
			self.settingsDialog.group_clipboard.setEnabled(True)

		self.settingsDialog.group_clipboard.radio_shortlink.setChecked(self.copy_shortlink)
		self.settingsDialog.group_clipboard.radio_publiclink.setChecked(self.copy_link)
		self.settingsDialog.group_clipboard.radio_dontcopy.setChecked(not self.copy_link and not self.copy_shortlink)
		self.settingsDialog.group_name.input_nameFormat.setText(self.nameFormat)
		self.settingsDialog.adjustSize()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("dropbox")
		self.access_token = settings.value("access-token", "")
		self.user_id = settings.value("user-id", "")
		self.display_name = settings.value("display-name", "")
		self.copy_shortlink = settings.value("copy-shortlink", "true") in ['true', True]
		self.copy_link = settings.value("copy-link", "true") in ['true', True]
		self.nameFormat = settings.value("name-format", "Screenshot at %H-%M-%S")
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("dropbox")
		settings.setValue("access-token", self.access_token)
		settings.setValue("user-id", self.user_id)
		settings.setValue("display-name", self.display_name)
		settings.setValue("copy-shortlink", self.settingsDialog.group_clipboard.radio_shortlink.checked)
		settings.setValue("copy-link", self.settingsDialog.group_clipboard.radio_publiclink.checked)
		settings.setValue("name-format", self.settingsDialog.group_name.input_nameFormat.text)
		settings.setValue("")
		settings.endGroup()
		settings.endGroup()
	
	def isConfigured(self):
		self.loadSettings()
		if not self.access_token:
			return False
		return True

	def getFilename(self):
		self.loadSettings()
		return ScreenCloud.formatFilename(self.nameFormat)
	      
	def upload(self, screenshot, name):
		self.loadSettings()
		timestamp = time.time()
		try:
			tmpFilename = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		except AttributeError:
			from PythonQt.QtCore import QStandardPaths #fix for Qt5
			tmpFilename = QStandardPaths.writableLocation(QStandardPaths.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())

		f = open(tmpFilename, 'rb')
		response = self.client.files_upload(f.read(), '/' + ScreenCloud.formatFilename(name))
		f.close()
		os.remove(tmpFilename)
		if self.copy_link:
			share = self.client.sharing_create_shared_link('/' + ScreenCloud.formatFilename(name), short_url=self.copy_shortlink)
			if self.copy_shortlink == False: # generate direct link
				ScreenCloud.setUrl('https://dl.dropboxusercontent' + share.url[19:-5])
			else:
				ScreenCloud.setUrl(share.url)

		return True

	def selectFolderClicked(self):
		self.selectFolderDialog.exec_()

	def startAuthenticationProcess(self):
		self.settingsDialog.group_account.widget_authorize.button_authenticate.setEnabled(False)
		self.flow = dropbox.oauth.DropboxOAuth2FlowNoRedirect('sfacmqvdb9dn66r', 'hx8meda636xgsox')
		authorize_url = QUrl(self.flow.start())
		QDesktopServices.openUrl(authorize_url)
		try:
			code = raw_input("Enter the authorization code from the dropbox website:")
		except NameError:
			code = input("Enter the authorization code from the dropbox website:")
		if code:
			try:
				oauth2_result = self.flow.finish(code)
				self.access_token = oauth2_result.access_token
				self.client = dropbox.Dropbox(self.access_token)
				account = self.client.users_get_current_account()
				self.user_id = account.account_id
				self.display_name = account.name.display_name
			except dropbox.auth.AccessError:
				if "win" in sys.platform: #Workaround for crash on windows
					self.parentWidget.hide()
					self.settingsDialog.hide()
				QMessageBox.critical(self.settingsDialog, "Failed to authenticate", "Failed to authenticate with Dropbox. Wrong code?")
				if "win" in sys.platform:
					self.settingsDialog.show()
					self.parentWidget.show()
		self.saveSettings()
		self.updateUi()

	def logout(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("dropbox")
		settings.remove("access-token")
		settings.remove("user-id")
		settings.remove("display-name")
		settings.endGroup()
		settings.endGroup()
		self.loadSettings()
		self.updateUi()

	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_name.label_example.setText(ScreenCloud.formatFilename(nameFormat))
