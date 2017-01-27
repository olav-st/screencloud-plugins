import ScreenCloud
from PythonQt.QtCore import QFile, QSettings
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices
from PythonQt.QtUiTools import QUiLoader
import subprocess, time, string, sys
from collections import defaultdict

class ShellUploader():
	def __init__(self):
		self.uil = QUiLoader()

	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.loadSettings()
		self.settingsDialog.group_shell.input_command.text = self.commandFormat
		self.settingsDialog.group_shell.output_is_url.checked = self.outputIsUrl
		self.settingsDialog.open()

	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("shell")
		self.commandFormat = settings.value("command", "")
		self.outputIsUrl = settings.value("copyOutput",str(False)) == "True"
		settings.endGroup()
		settings.endGroup()

	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("shell")
		settings.setValue("command", self.settingsDialog.group_shell.input_command.text)
		settings.setValue("copyOutput", str(self.settingsDialog.group_shell.output_is_url.checked))
		settings.endGroup()
		settings.endGroup()

	def isConfigured(self):
		self.loadSettings()
		if not self.commandFormat:
			return False
		return True

	def getFilename(self):
		timestamp = time.time()
		return ScreenCloud.formatFilename(str(timestamp))

	def upload(self, screenshot, name):
		self.loadSettings()
		try:
			tmpFilename = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + name
		except AttributeError:
			from PythonQt.QtCore import QStandardPaths #fix for Qt5
			tmpFilename = QStandardPaths.writableLocation(QStandardPaths.TempLocation) + "/" + name
		screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())
		command = string.Formatter().vformat(self.commandFormat, (), defaultdict(str, s = tmpFilename))
		try:
			command = command.encode(sys.getfilesystemencoding())
		except UnicodeEncodeError:
			ScreenCloud.setError("Invalid characters in command '" + command + "'")
			return False
		try:
			if self.outputIsUrl:
				pipe = subprocess.PIPE
			else:
				pipe = None


			p = subprocess.Popen(command, shell=True, stdout=pipe)
			p.wait()
			if p.returncode > 0:
				ScreenCloud.setError("Command " + command + " did not return 0")
				return False
			elif self.outputIsUrl:
				result = p.stdout.read()
				result = result.strip()
				ScreenCloud.setUrl(result)

		except OSError:
			ScreenCloud.setError("Failed to run command " + command)
			return False

		return True