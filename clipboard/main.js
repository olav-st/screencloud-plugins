loadQtBindings("qt.core", "qt.gui");

function init()
{
    ScreenCloud.setConfigured(true);
}
function loadSettings()
{
    //This plugin has no settings, since it simply copies to the clipboard'
    ScreenCloud.setConfigured(true);
    ScreenCloud.setFilename("Screenshot for clipboard");
}
function saveSettings()
{
    //This plugin has no settings, since it simply copies to the clipboard
}
function setupSettingsUi(preferencesDialog)
{
    QMessageBox.information(preferencesDialog, "Clipboard plugin", "This plugin has no settings. It will simply copy any screenshot to the system clipboard.");
}
function upload(screenshot)
{
    var clipboard = QApplication.clipboard();
    clipboard.setImage(screenshot);
    ScreenCloud.finished("");
}