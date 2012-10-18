loadQtBindings("qt.core" ,"qt.network");
var Dropbox;
if (Dropbox == null) {
    Dropbox = new Object;
}
Dropbox.netManager = new QNetworkAccessManager();
Dropbox.credentials = {};

Dropbox.replyFinished = function(reply)
{
    queryFinished = true;   
}
Dropbox.replyError = function(networkError)
{
    queryError = true;
}
Dropbox.sslErrors = function(reply, errors)
{
    print("SSL ERROR!11!");
}

Dropbox.netManager.finished.connect(Dropbox.replyFinished);
Dropbox.netManager.sslErrors.connect(Dropbox.sslErrors);

Dropbox.setCredentials = function(consumer_key, consumer_secret, access_token, access_token_secret) {
    Dropbox.credentials.consumerKey = consumer_key;
    Dropbox.credentials.consumerSecret = consumer_secret;
    Dropbox.credentials.token = access_token;
    Dropbox.credentials.tokenSecret = access_token_secret;
    Dropbox.credentials.signatures = {
        consumer_key: Dropbox.credentials.consumerKey,
        shared_secret: Dropbox.credentials.consumerSecret,
        oauth_token: Dropbox.credentials.token,
        oauth_secret: Dropbox.credentials.tokenSecret,
    };
}
Dropbox.getRequestToken = function()
{
    //oauth.setSignatureMethod("PLAINTEXT");
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.dropbox.com/1/oauth/request_token",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Dropbox.credentials.signatures
                            }
                       ); 
    var requestTokenReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
    var reply = Dropbox.netManager.get(requestTokenReq);
    reply.error.connect(Dropbox.replyError);

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
    var requestToken = getQueryVariable(replyText, "oauth_token");
    var requestTokenSecret = getQueryVariable(replyText, "oauth_token_secret");
    Dropbox.setCredentials(Dropbox.credentials.consumerKey, Dropbox.credentials.consumerSecret, requestToken, requestTokenSecret);
    return true;
}
Dropbox.getAuthorizeUrl = function()
{
    if(Dropbox.credentials.token == undefined || Dropbox.credentials.tokenSecret)
    {
        Dropbox.getRequestToken();
    }
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://www.dropbox.com/1/oauth/authorize",
                             parameters: [],
                             signatures: Dropbox.credentials.signatures
                            }
                       ); 
    return oauthSignedRequest.signed_url;
}
Dropbox.getAccessToken = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.dropbox.com/1/oauth/access_token",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Dropbox.credentials.signatures
                            }
                       );
    var accessTokenReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
    var reply = Dropbox.netManager.get(accessTokenReq);
    reply.error.connect(Dropbox.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    var accessToken = getQueryVariable(replyText, "oauth_token");
    var accessTokenSecret = getQueryVariable(replyText, "oauth_token_secret");
    if(queryError || isBlankOrEmpty(replyText) || !accessToken || !accessTokenSecret)
    {
        return false;
    }
    Dropbox.setCredentials(Dropbox.credentials.consumerKey, Dropbox.credentials.consumerSecret, accessToken, accessTokenSecret);
    return true;
}
Dropbox.getAccountInfo = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.dropbox.com/1/account/info",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Dropbox.credentials.signatures
                            }
                       );
    var accInfoReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
    var reply = Dropbox.netManager.get(accInfoReq);
    reply.error.connect(Dropbox.replyError);

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
Dropbox.uploadImage = function(name, image)
{
    var oauth = OAuthSimple();
    oauth.setAction("PUT");
    var oauthSignedRequest = oauth.sign(
                       { path: "https://api-content.dropbox.com/1/files_put/sandbox/" + encodeURI(name),
                         parameters: {oauth_method: "PLAINTEXT", overwrite: false},
                         method: "PLAINTEXT",
                         signatures: Dropbox.credentials.signatures
                        }
                   ); 
    var uploadImgReq = new QNetworkRequest( QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)) );
    uploadImgReq.setHeader(QNetworkRequest.ContentLengthHeader, image.size());
    var reply = Dropbox.netManager.put(uploadImgReq, image);
    //reply.error.connect(Dropbox.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    if(queryError)
    {
        if(!isBlankOrEmpty(replyText))
        {
            return JSON.parse(replyText);
        }
        return null;
    }
    return JSON.parse(replyText);
}
Dropbox.getPublicLink = function(filename)
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.dropbox.com/1/shares/sandbox/" + encodeURI(filename),
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Dropbox.credentials.signatures
                            }
                       );
    var publicLinkReq = new QNetworkRequest( QUrl.fromEncoded(new QByteArray(oauthSignedRequest.signed_url)) );
    var reply = Dropbox.netManager.get(publicLinkReq);
    reply.error.connect(Dropbox.replyError);

    queryFinished = false;
    queryError = false;
    var eventLoop = new QEventLoop();
    while (!queryFinished) {
       eventLoop.processEvents(QEventLoop.WaitForMoreEvents);
    }
    var replyText = qb2String(reply.readAll());
    if(queryError)
    {
        if(!isBlankOrEmpty(replyText))
        {
            return JSON.parse(replyText);
        }
        return null;
    }
    return JSON.parse(replyText).url;
}