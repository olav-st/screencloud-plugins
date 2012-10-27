loadQtBindings("qt.core", "qt.gui","qt.network");
include("date.format.js");
include("json2.js");
include("qb2string.js");
include("stringutils.js");
include("querystring.js");
include("OAuthSimple.js");
include("imgurapi.js");

var settingsWidget = loadUiFile("settings.ui");
settingsWidget.accepted.connect(saveSettings);

function init()
{
    Imgur.setCredentials(ScreenCloud.getConsumerKey("imgur"), ScreenCloud.getConsumerSecret("imgur"));
    Imgur.setApiKey(ScreenCloud.getApiKey("imgur"));
    settingsWidget.group_account.button_authorize.clicked.connect(authorizeButtonPressed);
    settingsWidget.group_account.button_logout.clicked.connect(logoutButtonClicked);
}
function loadSettings()
{
    settings.beginGroup("uploaders");
    settings.beginGroup("imgur"); //Load the settings for this uploader
    ScreenCloud.setConfigured(JSON.parse(settings.value("configured", false)));
    accessToken = Security.decrypt(settings.value("token", ""));
    accessTokenSecret = Security.decrypt(settings.value("token_secret", ""));
    loggedIn = !(isBlankOrEmpty(accessToken) || isBlankOrEmpty(accessTokenSecret));
    username = settings.value("username", "");
    anon = JSON.parse(settings.value("anon", true));
    copyImgurLink = JSON.parse(settings.value("copy_imgur_link", true)); //Parse string as JSON to get bool
    copyDirectLink = JSON.parse(settings.value("copy_direct_link", false));
    settings.endGroup(); //shortname
    settings.endGroup(); //uploaders

    settings.beginGroup("general"); //Load settings that is not specific to this uploader
    format = settings.value("format", "png").toString();
    jpegQuality = settings.value("jpeg-quality", 90);
    settings.endGroup();

    if(loggedIn)
    {
        Imgur.setCredentials(Imgur.credentials.consumerKey, Imgur.credentials.consumerSecret, accessToken, accessTokenSecret);
    }else
    {
        Imgur.credentials.token = null;
        Imgur.credentials.tokenSecret = null;
        Imgur.setCredentials(Imgur.credentials.consumerKey, Imgur.credentials.consumerSecret);
    }
    ScreenCloud.setFilename("Screenshot at " + new Date().format("yyyy-MM-dd hh:mm:ss"));
}
function saveSettings()
{
    anon = settingsWidget.group_account.radio_anon.checked;
    copyImgurLink = settingsWidget.group_clipboard.radio_imgur.checked;
    copyDirectLink = settingsWidget.group_clipboard.radio_directlink.checked;

    settings.beginGroup("uploaders");
    settings.beginGroup("imgur");
    settings.setValue("configured", true);
    settings.setValue("token", Security.encrypt(accessToken));
    settings.setValue("token_secret", Security.encrypt(accessTokenSecret));
    settings.setValue("username", username);
    settings.setValue("anon", settingsWidget.group_account.radio_anon.checked);
    settings.setValue("copy_imgur_link", settingsWidget.group_clipboard.radio_imgur.checked);
    settings.setValue("copy_direct_link", settingsWidget.group_clipboard.radio_directlink.checked);
    settings.endGroup(); //imgur
    settings.endGroup(); //uploaders
}
function setupSettingsUi(preferencesDialog)
{
    loadSettings();
    settingsWidget.setWindowTitle("Imgur settings");
    updateUi();
    settingsWidget.exec();
}
function updateUi()
{
    settingsWidget.group_account.label_loggedIn.setVisible(loggedIn);
    settingsWidget.group_account.label_user.setVisible(loggedIn);
    settingsWidget.group_account.button_logout.setVisible(loggedIn);
    settingsWidget.group_account.button_authorize.setVisible(!loggedIn);
    settingsWidget.group_account.radio_anon.setChecked(anon);
    settingsWidget.group_account.radio_account.setChecked(!anon);
    settingsWidget.group_clipboard.radio_imgur.setChecked(copyImgurLink);
    settingsWidget.group_clipboard.radio_directlink.setChecked(copyDirectLink);
    settingsWidget.group_clipboard.radio_dontcopy.setChecked(!(copyImgurLink || copyDirectLink));
    settingsWidget.group_clipboard.radio_dontcopy.setDisabled(anon);
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

    reply = Imgur.uploadImage(ScreenCloud.getFilename(), ba, anon);
    if(reply == null)
    {
        ScreenCloud.error("Failed to parse response from imgur api");
    }else if(reply.error != null)
    {
        ScreenCloud.error("Failed to upload to imgur. Error: " + reply.error.message);
    }else
    {
        var link = "";
        if(anon)
        {
            linkRoot = reply.upload.links;
        }else
        {
            linkRoot = reply.images.links;
        }
        if(copyImgurLink || copyDirectLink)
        {
            if(copyImgurLink)
            {
                link = linkRoot.imgur_page;
            }else
            {
                link = linkRoot.original;
            }
        }
        print("Imgur delete link: " + linkRoot.delete_page);
        ScreenCloud.finished(link);
    }
}
function authorizeButtonPressed()
{
    settingsWidget.group_account.button_authorize.text = "Waiting for authorization...";
    settingsWidget.group_account.button_authorize.setEnabled(false);
    settingsWidget.buttonBox.button(QDialogButtonBox.Save).setEnabled(false);
    QDesktopServices.openUrl(new QUrl(Imgur.getAuthorizeUrl()));
    while(settingsWidget.visible && !loggedIn)
    {
        if(settingsWidget.isActiveWindow)
        {
            if(Imgur.getAccessToken())
            {
                settingsWidget.buttonBox.button(QDialogButtonBox.Save).setEnabled(true);
                loggedIn = true;
                accessToken = Imgur.credentials.token;
                accessTokenSecret = Imgur.credentials.tokenSecret;
                username = Imgur.getAccountInfo().account.url;
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
        settings.beginGroup("imgur");
        settings.remove("token");
        settings.remove("token_secret");
        settings.remove("username");
        settings.endGroup(); //imgur
        settings.endGroup(); //uploaders
    }
    loadSettings();
    updateUi();
}