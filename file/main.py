import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QIODevice
from PythonQt.QtGui import QWidget, QDialog, QFileDialog
from PythonQt.QtUiTools import QUiLoader

class FileUploader():
	def __init__(self):
		self.uil = QUiLoader()
		self.loadSettings()
		
	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_name.input_name.connect("textChanged(QString)", self.nameFormatEdited)
		self.settingsDialog.group_location.button_browse.connect("clicked()", self.browseForFolder)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.loadSettings()
		self.settingsDialog.group_name.input_name.setText(self.nameFormat)
		self.settingsDialog.group_location.input_folder.setText(self.folder)
		self.settingsDialog.open()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("file")
		self.nameFormat = settings.value("name-format", "Screenshot at %H-%M-%S")
		self.folder = settings.value("folder", "")
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("file")
		settings.setValue("name-format", self.settingsDialog.group_name.input_name.text)
		settings.setValue("folder", self.settingsDialog.group_location.input_folder.text)
		settings.endGroup()
		settings.endGroup()
	
	def isConfigured(self):
		self.loadSettings()
		return self.folder and self.nameFormat

	def getFilename(self):
		self.loadSettings()
		return ScreenCloud.formatFilename(self.nameFormat)
	      
	def upload(self, screenshot, name):
		self.loadSettings()
		f = QFile(self.folder + "/" + ScreenCloud.formatFilename(name))
		f.open(QIODevice.WriteOnly)
		if not f.isWritable():
			ScreenCloud.setError("File " + f.fileName() + " is not writable!")
			return False
		screenshot.save(f, ScreenCloud.getScreenshotFormat())
		f.close()
		return True

	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_name.label_example.setText(ScreenCloud.formatFilename(nameFormat))

	def browseForFolder(self):
		selectedFolder = QFileDialog.getExistingDirectory(self.settingsDialog, "Select Folder...", self.folder)
		if selectedFolder:
			self.settingsDialog.group_location.input_folder.setText(selectedFolder)
			self.saveSettings()