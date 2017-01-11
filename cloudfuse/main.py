import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QUrl
from PythonQt.QtGui import QWidget, QDialog, QDesktopServices, QMessageBox
from PythonQt.QtUiTools import QUiLoader

import time, os, urllib2, json, base64
from base64 import b64encode
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

class CloudFuseUploader():
	def __init__(self):
		self.uil = QUiLoader()
		self.loadSettings()


	def upload_image(self, path=None, title=None):
		register_openers()

		# Create the request
		datagen, headers = multipart_encode({"file": open(path, "rb"), "title": title})
		request = urllib2.Request("https://cloudfuse.io/api/droplets", datagen, headers)

		# Set HTTP basic auth header
		base64string = base64.encodestring('%s:%s' % (self.email, self.password)).replace('\n', '')
		request.add_header("Authorization", "Basic %s" % base64string)   

		# Make the request
		result = urllib2.urlopen(request)

		# Return it
		data = json.load(result)
		return data


	def showSettingsUI(self, parentWidget):
		self.parentWidget = parentWidget
		self.settingsDialog = self.uil.load(QFile(workingDir + "/settings.ui"), parentWidget)
		self.settingsDialog.group_account.input_email.text = self.email
		self.settingsDialog.group_account.input_password.text = self.password
		self.settingsDialog.group_name.input_name.connect("textChanged(QString)", self.nameFormatEdited)
		self.settingsDialog.connect("accepted()", self.saveSettings)
		self.updateUi()
		self.settingsDialog.open()


	def updateUi(self):
		self.loadSettings()
		self.settingsDialog.group_account.input_email.setText(self.email)
		self.settingsDialog.group_account.input_password.setText(self.password)
		self.settingsDialog.group_name.input_name.setText(self.nameFormat)
		self.settingsDialog.adjustSize()


	def loadSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("cloudfuse")
		self.email = settings.value("email", "")
		self.password = settings.value("password", "")
		self.nameFormat = settings.value("name-format", "Screenshot at %H:%M:%S")
		settings.endGroup()
		settings.endGroup()


	def saveSettings(self):
		settings = QSettings()
		settings.beginGroup("uploaders")
		settings.beginGroup("cloudfuse")
		settings.setValue("email", self.settingsDialog.group_account.input_email.text)
		settings.setValue("password", self.settingsDialog.group_account.input_password.text)
		settings.setValue("name-format", self.settingsDialog.group_name.input_name.text)
		settings.endGroup()
		settings.endGroup()
	

	def isConfigured(self):
		self.loadSettings()
		if self.email and self.password:
			return True
		else:
			return False


	def getFilename(self):
		self.loadSettings()
		return ScreenCloud.formatFilename(self.nameFormat)
				

	def upload(self, screenshot, name):
		self.loadSettings()
		
		# Save to a temp file
		timestamp = time.time()
		tmpFilename = QDesktopServices.storageLocation(QDesktopServices.TempLocation) + "/" + ScreenCloud.formatFilename(str(timestamp))
		screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())
		
		# Upload!
		try:
			uploaded_image = self.upload_image(tmpFilename, title=ScreenCloud.formatFilename(name, False))
		except Exception as e:
			ScreenCloud.setError("Failed to upload to CloudFuse. " + e.message)
			return False
		ScreenCloud.setUrl(uploaded_image["url"])
		return True


	def nameFormatEdited(self, nameFormat):
		self.settingsDialog.group_name.label_example.setText(ScreenCloud.formatFilename(nameFormat, False))