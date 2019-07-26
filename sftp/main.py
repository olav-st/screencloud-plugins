import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QUrl
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QMessageBox, QFileDialog
from PythonQt.QtUiTools import QUiLoader
import time, sys, os.path, socket
import ssh2
from ssh2.session import Session
from ssh2.sftp import LIBSSH2_FXF_CREAT, LIBSSH2_FXF_WRITE, \
					  LIBSSH2_SFTP_S_IRUSR, LIBSSH2_SFTP_S_IRGRP, \
					  LIBSSH2_SFTP_S_IWUSR, LIBSSH2_SFTP_S_IROTH, \
					  LIBSSH2_SFTP_S_IXUSR

class SFTPUploader():
	def __init__(self):
		try:
			tempLocation = QDesktopServices.storageLocation(QDesktopServices.TempLocation)
		except AttributeError:
			from PythonQt.QtCore import QStandardPaths #fix for Qt5
			tempLocation = QStandardPaths.writableLocation(QStandardPaths.TempLocation)

		self.uil = QUiLoader()
		self.loadSettings()

	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_server.combo_auth.connect("currentIndexChanged(QString)", self.authMethodChanged)
		self.settingsDialog.group_server.button_browse.connect("clicked()", self.browseForKeyfile)
		self.settingsDialog.group_location.input_url.connect("textChanged(QString)", self.urlFormatEdited)
		self.settingsDialog.group_location.checkbox_url_extension.connect("stateChanged(int)", self.urlExtensionEdited)
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
		self.settingsDialog.group_location.input_name.text = self.nameFormat
		self.settingsDialog.group_location.checkbox_url_extension.checked = self.urlExtension
		self.settingsDialog.group_location.input_url.text = self.url
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
		self.urlExtension = settings.value("url-extension", "true") == "true"
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
		settings.setValue("url-extension", self.settingsDialog.group_location.checkbox_url_extension.isChecked())
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
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((self.host, self.port))
			session = Session()
			session.handshake(sock)
		except Exception as e:
			ScreenCloud.setError(e.message)
			return False
		if self.authMethod == "Password":
			try:
				session.userauth_password(self.username, self.password)
			except ssh2.exceptions.AuthenticationError:
				ScreenCloud.setError("Authentication failed (password)")
				return False
		else:
			try:
				session.userauth_publickey_fromfile(self.username, self.keyfile, passphrase=self.passphrase)
			except ssh2.exceptions.AuthenticationError:
				ScreenCloud.setError("Authentication failed (key)")
				return False
			except Exception as e:
				ScreenCloud.setError("Unknown error: " + e.message)
				return False
		sftp = session.sftp_init()
		mode = LIBSSH2_SFTP_S_IRUSR | \
			LIBSSH2_SFTP_S_IWUSR | \
			LIBSSH2_SFTP_S_IRGRP | \
			LIBSSH2_SFTP_S_IROTH
		f_flags = LIBSSH2_FXF_CREAT | LIBSSH2_FXF_WRITE
		try:
			try:
				sftp.opendir(self.folder)
			except ssh2.exceptions.SFTPError:
				sftp.mkdir(self.folder, mode | LIBSSH2_SFTP_S_IXUSR)
			(filepath, filename) = os.path.split(ScreenCloud.formatFilename(name))
			if len(filepath):
				for folder in filepath.split("/"):
					try:
						sftp.mkdir(folder)
					except IOError:
						pass
			source = tmpFilename
			destination = self.folder + "/" + ScreenCloud.formatFilename(filename)
			with open(source, 'rb') as local_fh, sftp.open(destination, f_flags, mode) as remote_fh:
				for data in local_fh:
					remote_fh.write(data)
		except IOError:
			ScreenCloud.setError("Failed to write " + self.folder + "/" + ScreenCloud.formatFilename(name) + ". Check permissions.")
			return False
		sock.close()
		if self.url:
			url = self.url + ScreenCloud.formatFilename(name)
			if not self.urlExtension:
				last_dot = url.rfind(".")
				if last_dot != -1:
					url = url[:last_dot]
			ScreenCloud.setUrl(url)
		return True

	def authMethodChanged(self, method):
		self.authMethod = method
		self.updateUi()

	def browseForKeyfile(self):
		filename = QFileDialog.getOpenFileName(self.settingsDialog, "Select Keyfile...", QDesktopServices.storageLocation(QDesktopServices.HomeLocation), "*")
		if filename:
			self.settingsDialog.group_server.input_keyfile.setText(filename)

	def urlFormatEdited(self, urlFormat):
		url = urlFormat + self.settingsDialog.group_location.label_name_example.text
		if not self.settingsDialog.group_location.checkbox_url_extension.isChecked():
			last_dot = url.rfind(".")
			if last_dot != -1:
				url = url[:last_dot]
		self.settingsDialog.group_location.label_url_example.setText(url)
	
	def urlExtensionEdited(self, urlExtension):
		self.urlFormatEdited(self.settingsDialog.group_location.input_url.text)

	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_location.label_name_example.setText(ScreenCloud.formatFilename(nameFormat))
		self.urlFormatEdited(self.settingsDialog.group_location.input_url.text)
