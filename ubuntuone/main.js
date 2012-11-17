loadQtBindings("qt.core", "qt.gui","qt.network");
include("date.format.js");
include("json2.js");
include("stringutils.js");
include("OAuthSimple.js");
include("date.format.js");
include("u1api.js");
var settingsWidget = loadUiFile("settings.ui", true);
settingsWidget.accepted.connect(saveSettings);
var selectFolderWidget = loadUiFile("selectFolder.ui", true);

function init()
{
    selectFolderWidget.tree_folders.expanded.connect(loadSubfolders);
    settingsWidget.group_location.button_selectFolder.clicked.connect(openSelectFolderDialog);
    settingsWidget.group_account.widget_login.button_login.clicked.connect(loginButtonClicked);
    settingsWidget.group_account.widget_loggedIn.button_logout.clicked.connect(logoutButtonClicked);
    settingsWidget.group_location.input_prefix.textEdited.connect(nameFormatEdited);
    settingsWidget.group_location.input_name.textEdited.connect(nameFormatEdited);
    settingsWidget.group_location.input_suffix.textEdited.connect(nameFormatEdited);
}
function loadSettings()
{
    settings.beginGroup("uploaders");
    settings.beginGroup("ubuntuone");
    ScreenCloud.setConfigured(JSON.parse(settings.value("configured", false)));
    consumerKey = Security.decrypt(settings.value("consumer_key", ""));
    consumerSecret = Security.decrypt(settings.value("consumer_secret", ""));
    token = Security.decrypt(settings.value("token", ""));
    tokenSecret = Security.decrypt(settings.value("token_secret"));
    username = settings.value("username", "");

    path = settings.value("path", "");
    content_path = settings.value("content_path", "");
    prefixFormat = settings.value("prefix-format",  "");
    suffixFormat = settings.value("suffix-format", "yyyy-mm-dd HH:MM:ss");
    screenshotName = settings.value("name", "Screenshot at ").toString();
    settings.endGroup();
    settings.endGroup();

    settings.beginGroup("general");
    format = settings.value("format", "png").toString();
    jpegQuality = settings.value("jpeg-quality", 90);
    settings.endGroup();

    if(isBlankOrEmpty(token) || isBlankOrEmpty(tokenSecret) || isBlankOrEmpty(consumerKey) || isBlankOrEmpty(consumerSecret))
    {
        configured = false;
        loggedIn = false;
    }else
    {
        loggedIn = true;
        if(!isBlankOrEmpty(path))
        {
            configured = true;
        }
    }
    ScreenCloud.setConfigured(configured);
    U1.setCredentials(consumerKey, consumerSecret, token, tokenSecret);
    ScreenCloud.setFilename(buildFilename(prefixFormat, screenshotName, suffixFormat));
}
function saveSettings()
{
    path = settingsWidget.group_location.input_folder.text;
    prefixFormat = settingsWidget.group_location.input_prefix.text;
    configured = loggedIn && !isBlankOrEmpty(path);

    settings.beginGroup("uploaders");
    settings.beginGroup("ubuntuone");
    settings.setValue("configured", configured);
    ScreenCloud.setConfigured(configured);
    settings.setValue("consumer_key", Security.encrypt(consumerKey));
    settings.setValue("consumer_secret", Security.encrypt(consumerSecret));
    settings.setValue("token", Security.encrypt(token));
    settings.setValue("token_secret", Security.encrypt(tokenSecret));
    settings.setValue("path", path);
    if(!isBlankOrEmpty(path) && loggedIn)
    {
        settings.setValue("content_path", U1.nodeInfo(path).content_path);
    }
    settings.setValue("prefix-format", prefixFormat);
    settings.setValue("name", screenshotName);
    settings.setValue("suffix-format", suffixFormat);
    settings.endGroup();
    settings.endGroup();
}
function setupSettingsUi(preferencesDialog)
{
    loadSettings();
    settingsWidget.setWindowTitle("Ubuntu One settings");
    //settingsWidget.setParent(preferencesDialog);
    updateSettingsUi();
    nameFormatEdited();
    settingsWidget.exec();
}
function updateSettingsUi()
{
    settingsWidget.buttonBox.button(QDialogButtonBox.Save).setEnabled(loggedIn);
    settingsWidget.group_account.widget_login.setVisible(!loggedIn);
    settingsWidget.group_account.widget_loggedIn.setVisible(loggedIn);
    if(loggedIn)
    {
        settingsWidget.group_account.widget_loggedIn.label_user.setText(username);
    }
    settingsWidget.group_location.input_folder.setText(path);
    settingsWidget.group_location.input_prefix.setText(prefixFormat);
    settingsWidget.group_location.input_name.setText(screenshotName);
    settingsWidget.group_location.input_suffix.setText(suffixFormat);
    settingsWidget.group_location.setEnabled(loggedIn);
    settingsWidget.resize(settingsWidget.sizeHint.w, settingsWidget.sizeHint.h);
}

function upload(screenshot)
{
    var ba = new QByteArray();
    var buffer = new QBuffer( ba );
    buffer.open(QIODevice.WriteOnly);
    screenshot.save( buffer, format ); // writes image into ba
    buffer.close();

    if(ScreenCloud.getFilename().indexOf("." + format) == -1)
    {
        ScreenCloud.setFilename(ScreenCloud.getFilename() + "." + format);
    }
    U1.putFile(content_path + "/" + ScreenCloud.getFilename(), ba, "image/" + format);
    ScreenCloud.finished(U1.setPublic(path + "/" + ScreenCloud.getFilename(), true));
}

function nameFormatEdited(text)
{
    prefixFormat = settingsWidget.group_location.input_prefix.text;
    screenshotName = settingsWidget.group_location.input_name.text;
    suffixFormat = settingsWidget.group_location.input_suffix.text;
    ScreenCloud.setFilename(buildFilename(prefixFormat, screenshotName, suffixFormat));
    settingsWidget.group_location.label_example.text = ScreenCloud.getFilename();
}
function buildFilename(prefixFormat, screenshotName, suffixFormat)
{
    var prefix = "";
    var suffix = "";
    if(!isBlankOrEmpty(prefixFormat))
    {
        prefix = new Date().format(prefixFormat);
    }
    if(!isBlankOrEmpty(suffixFormat))
    {
        suffix = new Date().format(suffixFormat);
    }
    return prefix + screenshotName + suffix + "." + format;
}

function loginButtonClicked()
{
    settingsWidget.group_account.widget_login.button_login.setEnabled(false);
    settingsWidget.group_account.widget_login.button_login.text = "Logging in...";
    credentials = U1.login(settingsWidget.group_account.widget_login.input_email.text, settingsWidget.group_account.widget_login.input_password.text);
    if(credentials == null || credentials == undefined)
    {
        settingsWidget.group_account.widget_login.button_login.setEnabled(true);
        settingsWidget.group_account.widget_login.button_login.text = "Login";
        QMessageBox.warning(settingsWidget, "Ubuntu one login", "Failed to login to Ubuntu One. Please check your email and password.");
        return;
    }
    token = credentials.oauth_token;
    tokenSecret = credentials.oauth_secret;
    consumerKey = credentials.consumer_key;
    consumerSecret = credentials.shared_secret;
    if( !(isBlankOrEmpty(token) || isBlankOrEmpty(tokenSecret) || isBlankOrEmpty(consumerKey) || isBlankOrEmpty(consumerSecret)) )
    {
        loggedIn = true;
        settings.beginGroup("uploaders");
        settings.beginGroup("ubuntuone");
        settings.setValue("username", U1.accountInfo().visible_name);
        settings.endGroup();
        settings.endGroup();
        saveSettings();
        loadSettings();
        updateSettingsUi();
    }else
    {
        print("Failed to login to Ubuntu One");
        QMessageBox.warning(settingsWidget, "Ubuntu one login", "Failed to login to Ubuntu One. Please check your email and password.");
    }
    
}

function openSelectFolderDialog()
{
    selectFolderWidget.modal = true;
    //Load root nodes (volumes)
    var volumes = U1.listVolumes();
    var foldersModel = new QStandardItemModel();
    
    for(var i = 0; i < volumes.length; i++)
    {
        var volume = volumes[i];
        var volumeItem = new QStandardItem(volume.path);
        volumeItem.setIcon(QIcon.fromTheme("drive-harddisk"));
        volumeItem.setData(volume.path, Qt.UserRole);
        volumeItem.insertRow(0, new QStandardItem("Loading..."));
        foldersModel.appendRow(volumeItem);
    }
    selectFolderWidget.tree_folders.setModel(foldersModel);
    if(selectFolderWidget.exec() == QDialog.Accepted)
    {
        var indexes = selectFolderWidget.tree_folders.selectionModel().selectedIndexes();
        var path = foldersModel.data(indexes[0], Qt.UserRole);
        print("Selected path: " + path);
        settingsWidget.group_location.input_folder.setText(path);
    }
}
function loadSubfolders(index)
{
    var foldersModel = selectFolderWidget.tree_folders.model();
    var parent = foldersModel.itemFromIndex(index);
    var parentFolderPath = foldersModel.data(index, Qt.UserRole);
    var folders = U1.listFolders(parentFolderPath);
    if(folders != null)
    {
        parent.removeRow(0); //Remove loading item
        for(var i = 0; i < folders.length; i++)
        {
            var folder = folders[i];
            var folderPathParts = folder.path.split('/');
            var folderName = folderPathParts[folderPathParts.length -1];
            var folderItem = new QStandardItem(folderName);
            folderItem.setData(folder.resource_path, Qt.UserRole); 
            folderItem.setIcon(QIcon.fromTheme("folder"));
            parent.insertRow(i, folderItem);
            if(folder.has_children)
            {
                folderItem.insertRow(0, new QStandardItem("Loading..."));
            }
        }
    }  
}
function logoutButtonClicked()
{
    var msgBox = new QMessageBox();
    msgBox.addButton(QMessageBox.Yes);
    msgBox.addButton(QMessageBox.No);
    msgBox.text = "Are you sure that you want to log out?";
    msgBox.icon = QMessageBox.Information;
    if(msgBox.exec() == QMessageBox.Yes)
    {
        loggedIn = false;
        settings.beginGroup("uploaders");
        settings.beginGroup("ubuntuone");
        settings.remove("token");
        settings.remove("token_secret");
        settings.remove("consumer_key");
        settings.remove("consumer_secret");
        settings.remove("username");
        settings.endGroup(); //dropbox
        settings.endGroup(); //uploaders
        settingsWidget.group_account.widget_login.input_password.text = "";
        settingsWidget.group_account.widget_login.input_email.text = "";
        settingsWidget.group_account.widget_login.button_login.setEnabled(true);
        settingsWidget.group_account.widget_login.button_login.text = "Login";
    }
    loadSettings();
    updateSettingsUi();
}
