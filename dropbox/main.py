import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QUrl
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QMessageBox, QInputDialog
from PythonQt.QtUiTools import QUiLoader
import dropbox, time, os

class DropboxUploader():
	def __init__(self):
		uil = QUiLoader()
		self.settingsDialog = uil.load(QFile(workingDir + "/settings.ui"))
		self.settingsDialog.group_account.widget_authorize.button_authenticate.connect("clicked()", self.startAuthenticationProcess)
		self.settingsDialog.group_account.widget_loggedIn.button_logout.connect("clicked()", self.logout)
		self.settingsDialog.group_name.input_nameFormat.connect("textChanged(QString)", self.nameFormatEdited)
		self.loadSettings()
		if self.access_token:
			self.client = dropbox.client.DropboxClient(self.access_token)
		
	def showSettingsUI(self):
		self.loadSettings()
		self.updateUi()
		if self.settingsDialog.exec_():
			self.saveSettings()

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

		self.settingsDialog.group_clipboard.radio_publiclink.setChecked(self.copy_link)
		self.settingsDialog.group_clipboard.radio_dontcopy.setChecked(not self.copy_link)
		self.settingsDialog.group_name.input_nameFormat.setText(self.nameFormat)
		self.settingsDialog.adjustSize()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("dropbox")
		self.access_token = settings.value("access-token", "")
		self.user_id = settings.value("user-id", "")
		self.display_name = settings.value("display-name", "")
		self.copy_link = settings.value("copy-link", "true") in ['true']
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
		settings.setValue("copy-link", self.settingsDialog.group_clipboard.radio_publiclink.checked)
		settings.setValue("name-format", self.settingsDialog.group_name.input_nameFormat.text)
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
		tmpFilename = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())

		f = open(tmpFilename, 'rb')
		response = self.client.put_file('/' + ScreenCloud.formatFilename(name), f)
		f.close()
		os.remove(tmpFilename)
		if self.copy_link:
			share = self.client.share('/' + ScreenCloud.formatFilename(name))
			ScreenCloud.setUrl(share['url'])

		return True

	def selectFolderClicked(self):
		self.selectFolderDialog.exec_()

	def startAuthenticationProcess(self):
		self.settingsDialog.group_account.widget_authorize.button_authenticate.setEnabled(False)
		self.flow = dropbox.client.DropboxOAuth2FlowNoRedirect('sfacmqvdb9dn66r', 'hx8meda636xgsox')
		authorize_url = QUrl(self.flow.start())
		QDesktopServices.openUrl(authorize_url)
		code = QInputDialog.getText(self.settingsDialog, "Enter Dropbox Code", "Enter the authorization code from the dropbox website:")
		if code:
			try:
				self.access_token, self.user_id = self.flow.finish(code)
			except dropbox.rest.ErrorResponse:
				QMessageBox.critical(0, "Failed to authenticate", "Failed to authenticate with Dropbox. Wrong code?")
				self.settingsDialog.group_account.widget_authorize.input_code.setText("")
				return
			self.client = dropbox.client.DropboxClient(self.access_token)
			self.display_name = self.client.account_info()['display_name']
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