import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QUrl
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QMessageBox, QFileDialog
from PythonQt.QtUiTools import QUiLoader
import paramiko, time, sys

class SFTPUploader():
	def __init__(self):
		try:
			tempLocation = QDesktopServices.storageLocation(QDesktopServices.TempLocation)
		except AttributeError:
			from PythonQt.QtCore import QStandardPaths #fix for Qt5
			tempLocation = QStandardPaths.writableLocation(QStandardPaths.TempLocation)

		paramiko.util.log_to_file(tempLocation + "/screencloud-sftp.log")
		self.uil = QUiLoader()
		self.loadSettings()
		
	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_server.combo_auth.connect("currentIndexChanged(QString)", self.authMethodChanged)
		self.settingsDialog.group_server.button_browse.connect("clicked()", self.browseForKeyfile)
		self.settingsDialog.group_location.input_name.connect("textChanged(QString)", self.nameFormatEdited)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.loadSettings()
		self.updateUi()
		self.settingsDialog.group_server.input_host.text = self.host
		self.settingsDialog.group_server.input_port.value = self.port
		self.settingsDialog.group_server.input_username.text = self.username
		self.settingsDialog.group_server.input_password.text = self.password
		self.settingsDialog.group_server.input_keyfile.text = self.keyfile
		self.settingsDialog.group_server.input_passphrase.text = self.passphrase
		self.settingsDialog.group_location.input_folder.text = self.folder
		self.settingsDialog.group_location.input_url.text = self.url
		self.settingsDialog.group_location.input_name.text = self.nameFormat
		self.settingsDialog.group_server.combo_auth.setCurrentIndex(self.settingsDialog.group_server.combo_auth.findText(self.authMethod))
		self.settingsDialog.open()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("sftp")
		self.host = settings.value("host", "")
		self.port = int(settings.value("port", 22))
		self.username = settings.value("username", "")
		self.password = settings.value("password", "")
		self.keyfile = settings.value("keyfile", "")
		self.passphrase = settings.value("passphrase", "")
		self.url = settings.value("url", "")
		self.folder = settings.value("folder", "")
		self.nameFormat = settings.value("name-format", "Screenshot at %H-%M-%S")
		self.authMethod = settings.value("auth-method", "Password")
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("sftp")
		settings.setValue("host", self.settingsDialog.group_server.input_host.text)
		settings.setValue("port", int(self.settingsDialog.group_server.input_port.value))
		settings.setValue("username", self.settingsDialog.group_server.input_username.text)
		settings.setValue("password", self.settingsDialog.group_server.input_password.text)
		settings.setValue("keyfile", self.settingsDialog.group_server.input_keyfile.text)
		settings.setValue("passphrase", self.settingsDialog.group_server.input_passphrase.text)
		settings.setValue("url", self.settingsDialog.group_location.input_url.text)
		settings.setValue("folder", self.settingsDialog.group_location.input_folder.text)
		settings.setValue("name-format", self.settingsDialog.group_location.input_name.text)
		settings.setValue("auth-method", self.settingsDialog.group_server.combo_auth.currentText)
		settings.endGroup()
		settings.endGroup()

	def updateUi(self):
		self.settingsDialog.group_server.label_password.setVisible(self.authMethod == "Password")
		self.settingsDialog.group_server.input_password.setVisible(self.authMethod == "Password")
		self.settingsDialog.group_server.label_keyfile.setVisible(self.authMethod == "Key")
		self.settingsDialog.group_server.input_keyfile.setVisible(self.authMethod == "Key")
		self.settingsDialog.group_server.button_browse.setVisible(self.authMethod == "Key")
		self.settingsDialog.group_server.label_passphrase.setVisible(self.authMethod == "Key")
		self.settingsDialog.group_server.input_passphrase.setVisible(self.authMethod == "Key")
		self.settingsDialog.adjustSize()
	
	def isConfigured(self):
		self.loadSettings()
		return not(not self.host or not self.username or not (self.password or self.keyfile) or not self.folder)

	def getFilename(self):
		self.loadSettings()
		return ScreenCloud.formatFilename(self.nameFormat)
	      
	def upload(self, screenshot, name):
		self.loadSettings()
		#Save to a temporary file
		timestamp = time.time()
		try:
			tmpFilename = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		except AttributeError:
			from PythonQt.QtCore import QStandardPaths #fix for Qt5
			tmpFilename = QStandardPaths.writableLocation(QStandardPaths.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())
		#Connect to server
		try:
			transport = paramiko.Transport((self.host, self.port))
		except Exception as e:
			ScreenCloud.setError(e.message)
			return False
		if self.authMethod == "Password":
			try:
				transport.connect(username = self.username, password = self.password)
			except paramiko.AuthenticationException:
				ScreenCloud.setError("Authentication failed (password)")
				return False
		else:
			try:
				private_key = paramiko.RSAKey.from_private_key_file(self.keyfile, password=self.passphrase)
				transport.connect(username=self.username, pkey=private_key)
			except paramiko.AuthenticationException:
				ScreenCloud.setError("Authentication failed (key)")
				return False
			except paramiko.SSHException as e:
				ScreenCloud.setError("Error while connecting to " + self.host + ":" + str(self.port) + ". " + e.message)
				return False
			except Exception as e:
				ScreenCloud.setError("Unknown error: " + e.message)
				return False
		sftp = paramiko.SFTPClient.from_transport(transport)
		try:
			sftp.put(tmpFilename, self.folder + "/" + ScreenCloud.formatFilename(name))
		except IOError:
			ScreenCloud.setError("Failed to write " + self.folder + "/" + ScreenCloud.formatFilename(name) + ". Check permissions.")
			return False
		sftp.close()
		transport.close()
		if self.url:
			ScreenCloud.setUrl(self.url + ScreenCloud.formatFilename(name))
		return True

	def authMethodChanged(self, method):
		self.authMethod = method
		self.updateUi()

	def browseForKeyfile(self):
		filename = QFileDialog.getOpenFileName(self.settingsDialog, "Select Keyfile...", QDesktopServices.storageLocation(QDesktopServices.HomeLocation), "*")
		if filename:
			self.settingsDialog.group_server.input_keyfile.setText(filename)

	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_location.label_example.setText(ScreenCloud.formatFilename(nameFormat))
