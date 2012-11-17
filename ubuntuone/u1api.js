loadQtBindings("qt.core", "qt.network");
//include("oauth.js");

var U1;
if (U1 == null) {
    U1 = new Object;
}
U1.netManager = new QNetworkAccessManager();
U1.credentials = {};

U1.replyFinished = function(reply)
{
    queryFinished = true;
}
U1.replyError = function(networkError)
{
    queryError = true;
}
U1.authRequired = function(request, authenticator)
{
    print("Auth required");
    if(!loginAttempted)
    {
        authenticator.setUser(U1.credentials.email);
        authenticator.setPassword(U1.credentials.password);
        loginAttempted = true;
    }else
    {
        print("Login failed");
    }
}

U1.netManager.finished.connect(U1.replyFinished);
U1.netManager.authenticationRequired.connect(U1.authRequired);
loginAttempted = false;

U1.setCredentials = function(consumerKey, consumerSecret, accessToken, accessTokenSecret) {
    U1.credentials.consumerKey = consumerKey;
    U1.credentials.cosumerSecret = consumerSecret;
    U1.credentials.token = accessToken;
    U1.credentials.tokenSecret = accessTokenSecret;

    U1.credentials.signatures = {
        consumer_key: consumerKey,
        shared_secret: consumerSecret,
        oauth_token: accessToken,
        oauth_secret: accessTokenSecret,
    }

}
U1.getCredentials = function(email, password)
{
    loginAttempted = false;
    U1.credentials.email = email;
    U1.credentials.password = password;
    var accesTokenUrl = new QUrl("https://login.ubuntu.com/api/1.0/authentications");
    accesTokenUrl.addQueryItem("ws.op", "authenticate");
    accesTokenUrl.addQueryItem("token_name", "Ubuntu One @ " + QHostInfo.localHostName() + " [ScreenCloud]");
    accessTokenReq = new QNetworkRequest(accesTokenUrl);
    var reply = U1.netManager.get(accessTokenReq);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    if(queryError)
    {
        return null;
    }
    var replyText = qb2String(reply.readAll());
    var replyObj = JSON.parse(replyText);
    consumerSecret = replyObj.consumer_secret;
    consumerKey = replyObj.consumer_key;
    token = replyObj.token;
    tokenSecret = replyObj.token_secret;
    U1.setCredentials(consumerKey, consumerSecret, token, tokenSecret);
    return U1.credentials.signatures;
}
U1.copySSOToken = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://one.ubuntu.com/oauth/sso-finished-so-get-tokens/",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    var tokenCopyReq = new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    var reply = U1.netManager.get(tokenCopyReq);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    if(queryError)
    {
        return false;
    }
    return true;
}
U1.login = function(email, password)
{
    var credentials = U1.getCredentials(email, password);
    if(U1.copySSOToken())
    {
        return credentials;
    }else
    return null;
}
U1.accountInfo = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://one.ubuntu.com/api/file_storage/v1",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    var accInfoReq = new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    var reply = U1.netManager.get(accInfoReq);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    if(queryError)
    {
        return null;
    }

    return JSON.parse(replyText);
}
U1.nodeInfo = function(path, children)
{
   path = path.replace(/^\/|\/$/g, ''); //Remove any leading or trailing slashes
    if(path.indexOf("~/") == -1)
    {
        path = "~/" + path;
    }
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://one.ubuntu.com/api/file_storage/v1/" + encodeURI(path),
                             parameters: {oauth_method: "PLAINTEXT", include_children: children},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    var fileInfoReq = new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    var reply = U1.netManager.get(fileInfoReq);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    if(queryError)
    {
        return null;
    }
    var replyText = qb2String(reply.readAll());
    return JSON.parse(replyText);
}
U1.fileExists = function(volume, path)
{
    if(volume.indexOf("~/") == -1)
    {
        volume = "~/" + volume;
    }
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://one.ubuntu.com/api/file_storage/v1/" + encodeURI(volume) + "/" + encodeURI(path),
                             parameters: {oauth_method: "PLAINTEXT", include_children: children},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    fileInfoReq = new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    reply = U1.netManager.get(fileInfoReq);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    if(queryError)
    {
        return false;
    }
    var replyText = qb2String(reply.readAll());
    return !isBlankOrEmpty(replyText);
}
U1.listVolumes = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://one.ubuntu.com/api/file_storage/v1/volumes",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    volumeListReq = new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    print("listVolumes url: " + oauthSignedRequest.signed_url);
    reply = U1.netManager.get(volumeListReq);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    if(queryError)
    {
        return null;
    }
    var listObj = JSON.parse(replyText);
    return listObj;
}
U1.listFolders = function(path)
{
    var listObj = U1.nodeInfo(path, true);
    var folders = new Array();
    for(var i = 0; i < listObj.children.length; i++)
    {
        if(listObj.children[i].kind == "directory")
        {
            folders.push(listObj.children[i]);
        }
    }
    return folders;
}
U1.putFile = function(content_path, data, contentType)
{
    content_path = content_path.replace(/^\/|\/$/g, ''); //Remove any leading or trailing slashes
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://files.one.ubuntu.com/" + encodeURI(content_path),
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    var putFileReq =  new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    putFileReq.setHeader(QNetworkRequest.ContentLengthHeader, data.size());
    putFileReq.setHeader(QNetworkRequest.ContentTypeHeader, contentType);
    reply = U1.netManager.put(putFileReq, data);
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    if(queryError)
    {
        return false;
    }
    return true;
}
U1.setPublic = function(path, pub)
{
    path = path.replace(/^\/|\/$/g, ''); //Remove any leading or trailing slashes
    var jsonObj = { is_public: pub };
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://one.ubuntu.com/api/file_storage/v1/" + encodeURI(path),
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: U1.credentials.signatures
                            }
                       );
    var setPublicReq =  new QNetworkRequest(QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)));
    setPublicReq.setHeader(QNetworkRequest.ContentTypeHeader, "application/json");
    reply = U1.netManager.put(setPublicReq, new QByteArray(JSON.stringify(jsonObj)));
    reply.error.connect(U1.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    if(queryError)
    {
        return null;
    }
    var replyObj = JSON.parse(replyText);
    return replyObj.public_url;
}