loadQtBindings("qt.core", "qt.gui","qt.network");
include("date.format.js");
include("json2.js");
include("qb2string.js");
include("stringutils.js");
include("querystring.js");
include("OAuthSimple.js");
include("dropboxapi.js");

var settingsWidget = loadUiFile("settings.ui");
settingsWidget.accepted.connect(saveSettings);

function init()
{
    Dropbox.setCredentials(ScreenCloud.getConsumerKey("dropbox"), ScreenCloud.getConsumerSecret("dropbox"));
}
function loadSettings()
{
    settings.beginGroup("uploaders");
    settings.beginGroup("dropbox"); //Load the settings for this uploader
    accessToken = Security.decrypt(settings.value("token", ""));
    accessTokenSecret = Security.decrypt(settings.value("token_secret", ""));
    loggedIn = !(isBlankOrEmpty(accessToken) || isBlankOrEmpty(accessTokenSecret));
    username = settings.value("username", "");
    copyLink = JSON.parse(settings.value("copy_link", true)); //Parse the string as json to convert to bool
    settings.endGroup(); //shortname
    settings.endGroup(); //uploaders

    settings.beginGroup("general"); //Load settings that is not specific to this uploader
    format = settings.value("format", "png").toString();
    jpegQuality = settings.value("jpeg-quality", 90);
    settings.endGroup();

    if(loggedIn)
    {
        Dropbox.setCredentials(Dropbox.credentials.consumerKey, Dropbox.credentials.consumerSecret, accessToken, accessTokenSecret);
    }else
    {
        Dropbox.credentials.token = null;
        Dropbox.credentials.tokenSecret = null;
        Dropbox.setCredentials(Dropbox.credentials.consumerKey, Dropbox.credentials.consumerSecret);
    }
    ScreenCloud.setFilename("Screenshot at " + new Date().format("yyyy-MM-dd hh:mm:ss") + "." + format);
    ScreenCloud.setConfigured(loggedIn);
}
function saveSettings()
{
    settings.beginGroup("uploaders");
    settings.beginGroup("dropbox");
    settings.setValue("token", Security.encrypt(accessToken));
    settings.setValue("token_secret", Security.encrypt(accessTokenSecret));
    settings.setValue("username", username);
    settings.setValue("copy_link", !settingsWidget.group_clipboard.radio_dontcopy.checked);
    settings.endGroup(); //dropbox
    settings.endGroup(); //uploaders
}
function setupSettingsUi(preferencesDialog)
{
    loadSettings();
    settingsWidget.setWindowTitle("Dropbox settings");
    settingsWidget.group_account.button_authorize.clicked.connect(authorizeButtonPressed);
    settingsWidget.group_account.button_logout.clicked.connect(logoutButtonClicked);
    updateUi();
    settingsWidget.exec();
}
function updateUi()
{
    settingsWidget.buttonBox.button(QDialogButtonBox.Save).setEnabled(loggedIn);
    settingsWidget.group_account.label_loggedIn.setVisible(loggedIn);
    settingsWidget.group_account.label_user.setVisible(loggedIn);
    settingsWidget.group_account.button_logout.setVisible(loggedIn);
    settingsWidget.group_account.button_authorize.setVisible(!(loggedIn));
    settingsWidget.group_clipboard.radio_publiclink.setChecked(copyLink);
    settingsWidget.group_clipboard.radio_dontcopy.setChecked(!copyLink);
    settingsWidget.group_clipboard.setEnabled(loggedIn);
    if(loggedIn)
    {
        settingsWidget.group_account.label_user.text = username;
    }
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
    reply = Dropbox.uploadImage(ScreenCloud.getFilename(), ba);
    if(reply == null)
    {
        ScreenCloud.error("Failed to parse response from dropbox api");
    }else if(reply.error != null)
    {
        ScreenCloud.error("Failed to upload to dropbox. Error: " + reply.error);
    }else
    {
        if(!copyLink)
        {
            ScreenCloud.finished("");   
        }else
        {
            ScreenCloud.finished(Dropbox.getPublicLink(reply.path));
        }
    }
}
function authorizeButtonPressed()
{
    settingsWidget.group_account.button_authorize.text = "Waiting for authorization...";
    settingsWidget.group_account.button_authorize.setEnabled(false);
    QDesktopServices.openUrl(new QUrl(Dropbox.getAuthorizeUrl()));
    while(settingsWidget.visible && !loggedIn)
    {
        if(settingsWidget.isActiveWindow)
        {
            if(Dropbox.getAccessToken())
            {
                loggedIn = true;
                accessToken = Dropbox.credentials.token;
                accessTokenSecret = Dropbox.credentials.tokenSecret;
                username = Dropbox.getAccountInfo().display_name;
                saveSettings();
            }
        }
        var waitTime = QTime.currentTime().addSecs(1);
        while( QTime.currentTime() < waitTime )
            QCoreApplication.processEvents(QEventLoop.AllEvents, 100);  
    }
    updateUi();
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
        settings.beginGroup("dropbox");
        settings.remove("token");
        settings.remove("token_secret");
        settings.remove("username");
        settings.endGroup(); //dropbox
        settings.endGroup(); //uploaders
    }
    loadSettings();
    updateUi();
}