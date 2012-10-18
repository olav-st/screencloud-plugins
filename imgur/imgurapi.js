loadQtBindings("qt.core" ,"qt.network");
var Imgur;
if (Imgur == null) {
    Imgur = new Object;
}
Imgur.netManager = new QNetworkAccessManager();
Imgur.credentials = {};

Imgur.replyFinished = function(reply)
{
    queryFinished = true;   
}
Imgur.replyError = function(networkError)
{
    print(networkError.errorString);
    queryError = true;
}
Imgur.sslErrors = function(reply, errors)
{
    print("SSL ERROR!11!");
}

Imgur.netManager.finished.connect(Imgur.replyFinished);
Imgur.netManager.sslErrors.connect(Imgur.sslErrors);

Imgur.setCredentials = function(consumer_key, consumer_secret, access_token, access_token_secret) {
    Imgur.credentials.consumerKey = consumer_key;
    Imgur.credentials.consumerSecret = consumer_secret;
    Imgur.credentials.token = access_token;
    Imgur.credentials.tokenSecret = access_token_secret;
    Imgur.credentials.signatures = {
        consumer_key: Imgur.credentials.consumerKey,
        shared_secret: Imgur.credentials.consumerSecret,
        oauth_token: Imgur.credentials.token,
        oauth_secret: Imgur.credentials.tokenSecret,
    }
}
Imgur.setApiKey = function(api_key)
{
    Imgur.credentials.apiKey = api_key;
}
Imgur.getRequestToken = function()
{
    //oauth.setSignatureMethod("PLAINTEXT");
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.imgur.com/oauth/request_token",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Imgur.credentials.signatures
                            }
                       ); 
    print(oauthSignedRequest.signed_url);
    var requestTokenReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
    var reply = Imgur.netManager.get(requestTokenReq);
    reply.error.connect(Imgur.replyError);

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
    Imgur.setCredentials(Imgur.credentials.consumerKey, Imgur.credentials.consumerSecret, requestToken, requestTokenSecret);
    return true;
}
Imgur.getAuthorizeUrl = function()
{
    if(isBlankOrEmpty(Imgur.credentials.token) || isBlankOrEmpty(Imgur.credentials.tokenSecret))
    {
        Imgur.getRequestToken();
    }
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.imgur.com/oauth/authorize",
                             parameters: [],
                             signatures: Imgur.credentials.signatures
                            }
                       ); 
    print(oauthSignedRequest.signed_url);
    return oauthSignedRequest.signed_url;
}
Imgur.getAccessToken = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "https://api.imgur.com/oauth/access_token",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Imgur.credentials.signatures
                            }
                       );
    print(oauthSignedRequest.signed_url); 
    var accessTokenReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
    var reply = Imgur.netManager.get(accessTokenReq);
    reply.error.connect(Imgur.replyError);

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
    var accessToken = getQueryVariable(replyText, "oauth_token");
    var accessTokenSecret = getQueryVariable(replyText, "oauth_token_secret");
    Imgur.setCredentials(Imgur.credentials.consumerKey, Imgur.credentials.consumerSecret, accessToken, accessTokenSecret, "access_token");
    return true;
}
Imgur.getAccountInfo = function()
{
    var oauthSignedRequest = OAuthSimple().sign(
                           { path: "http://api.imgur.com/2/account.json",
                             parameters: {oauth_method: "PLAINTEXT"},
                             method: "PLAINTEXT",
                             signatures: Imgur.credentials.signatures
                            }
                       );
    var accInfoReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
    var reply = Imgur.netManager.get(accInfoReq);
    reply.error.connect(Imgur.replyError);

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
Imgur.uploadImage = function(name, image, anonymous)
{
    if(anonymous)
    {
        var url = new QUrl("http://api.imgur.com/2/upload.json");
        url.addQueryItem("key", Imgur.credentials.apiKey);
        url.addQueryItem("name", name);
        var request = new QNetworkRequest(url);
        var reply = Imgur.netManager.put(request, image.toBase64());
        reply.error.connect(Imgur.replyError);
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
    }else
    {
        var oauthSignedRequest = OAuthSimple().sign(
                           { path: "http://api.imgur.com/2/account/images.json",
                             parameters: {oauth_method: "PLAINTEXT", type: "base64", name: encodeURI(name)},
                             method: "PLAINTEXT",
                             signatures: Imgur.credentials.signatures
                            }
                       ); 
        print(oauthSignedRequest.signed_url);
        var uploadImgReq = new QNetworkRequest(new QUrl(oauthSignedRequest.signed_url));
        var reply = Imgur.netManager.post(uploadImgReq, image.toBase64());
        reply.error.connect(Imgur.replyError);

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
        print(replyText);
        return JSON.parse(replyText);
    }
}