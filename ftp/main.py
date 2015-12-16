import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QBuffer, QIODevice
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QIcon, QStandardItem, QStandardItemModel
from PythonQt.QtUiTools import QUiLoader
import ftplib, time

class FTPUploader():
	def __init__(self):
		self.uil = QUiLoader()
		
	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_location.input_name.connect("textChanged(QString)", self.nameFormatEdited)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.loadSettings()
		self.settingsDialog.group_server.input_host.text = self.host
		self.settingsDialog.group_server.input_port.value = self.port
		self.settingsDialog.group_server.input_username.text = self.username
		self.settingsDialog.group_server.input_password.text = self.password
		self.settingsDialog.group_server.input_url.text = self.url
		self.settingsDialog.group_location.input_folder.text = self.folder
		self.settingsDialog.group_location.input_name.text = self.nameFormat
		self.settingsDialog.open()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("ftp")
		self.host = settings.value("host", "")
		self.port = int(settings.value("port", 21))
		self.username = settings.value("username", "")
		self.password = settings.value("password", "")
		self.url = settings.value("url", "")
		self.folder = settings.value("folder", "")
		self.nameFormat = settings.value("name-format", "Screenshot at %H-%M-%S")
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("ftp")
		settings.setValue("host", self.settingsDialog.group_server.input_host.text)
		settings.setValue("port", int(self.settingsDialog.group_server.input_port.value))
		settings.setValue("username", self.settingsDialog.group_server.input_username.text)
		settings.setValue("password", self.settingsDialog.group_server.input_password.text)
		settings.setValue("url", self.settingsDialog.group_server.input_url.text)
		settings.setValue("folder", self.settingsDialog.group_location.input_folder.text)
		settings.setValue("name-format", self.settingsDialog.group_location.input_name.text)
		settings.endGroup()
		settings.endGroup()
	
	def isConfigured(self):
		self.loadSettings()
		return not(not self.host or not self.username or not self.password or not self.folder)

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

		ftp = ftplib.FTP()
		ftp.connect(self.host, self.port)
		ftp.login(self.username, self.password)
		f = open(tmpFilename, 'rb')
		try:
			ftp.cwd(self.folder)
		except ftplib.error_perm as err:
			ScreenCloud.setError(err.message)
			return False
		try:
			ftp.storbinary('STOR ' + name, f)
		except ftplib.error_perm as err:
			ScreenCloud.setError(err.message)
			return False
		ftp.quit()
		f.close()
		if self.url:
			ScreenCloud.setUrl(self.url + ScreenCloud.formatFilename(name))
		return True

	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_location.label_example.setText(ScreenCloud.formatFilename(nameFormat))
