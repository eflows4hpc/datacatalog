// This file will contain functions to manage authentication (including the token storage and access)

/************************************************
 * Event Listeners for XMLHttpRequests
 ************************************************/

// XMLHttpRequest EVENTLISTENER: if the call was successful, store the token locally and reload login page
function setLoginToken() {
    console.log("Response to login POST: " + this.responseText);
    if (this.status >= 400) {
        alert("The username and/ or the password is invalid!");
        logout();
    } else {
        var tokenData = JSON.parse(this.responseText);
        window.sessionStorage.auth_token = tokenData.access_token;
        getInfo(true);
        location.reload();
    }
}

// To be called by an inline XMLHttpRequest EVENTLISTENER: if the call was successful, update the userdata
function setUserdata(data, updateView) {
    console.log("Response to auth verification GET: " + data.responseText + " with status " + data.status);
    if (data.status >= 400) {
        console.log("Auth verification returned a " + data.status + " status. Reattempt login.");
        relog();
    } else {
        var userdata = JSON.parse(data.responseText);
        // store username and email in sessionData (blind overwrite if exists)
        window.sessionStorage.username = userdata.username;
        window.sessionStorage.email = userdata.email;
        if (updateView) {
            $('#usernameLabel').html(window.sessionStorage.username);
            $('#emailLabel').html(window.sessionStorage.email);
        }
    }
}

/*
* makes a post call for the token and stores it in localstorage
*/
function loginPOST(username, password) {
    var fullUrl = apiUrl + "token";
    console.log("Sending POST request to  " + fullUrl + " for login.")
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setLoginToken);
    xmlhttp.open("POST", fullUrl);
    xmlhttp.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xmlhttp.send("username=" + encodeURIComponent(username) + "&password=" + encodeURIComponent(password));
}

/**
 * logs out, and then redirects to the login page.
 */
function relog() {
    logout();
    window.location.href = "/login.html?relog=true";
}

/**
* checks the textfields for username and password, gives an error message if not given, then calls the loginPOST(username, password) function 
*/
function login() {
    $('#loginButton').prepend('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
    $('#loginButton').attr("disabled", true);
    loginPOST($('#usernameField').val(), $('#passwordField').val());
}


/*
* clear sessionStorage of all auth related data and redirect to the login page
*/
function logout() {
    delete window.sessionStorage.auth_token;
    delete window.sessionStorage.username;
    delete window.sessionStorage.email;
    location.reload();
}

/* 
* call API/me to get ifo about the user and check if token is valid
* if updateView is true, also update the username and email fields in the login page (with data from the sessionstorage)
* The function returns true if the token is valid and the server responded with the desired data
*/
function getInfo(updateView=false) {
    if (window.sessionStorage.auth_token === undefined) {
        return false;
    } else {
        // if updateView, set text to spinners, eventlistener will fill correct values
        if (updateView) {
            $('#usernameLabel').append('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
            $('#emailLabel').append('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        }

        // start GET /me, pass wether an update of the user labels is needed
        var fullUrl = apiUrl + "me";
        console.log("Sending GET request to  " + fullUrl + " for verifying authentication.")
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.open("GET", fullUrl);
        xmlhttp.setRequestHeader('Authorization', 'Bearer ' + window.sessionStorage.auth_token);
        xmlhttp.addEventListener("loadend", async function() {
            setUserdata(this, updateView);
        });
        xmlhttp.updateView = updateView;
        xmlhttp.send();
        return true; // this true is okay, if the request fails, it will automatically logout and reload anyway
    }
}

/*
* either show the userinfo table (true) or the loginform (false) (if present)
* also adjust the Log In Navbar element
* also show edit/ save and addNew Buttons (true) (if present)
*/
function showElementsDependingOnLoginStatus(loggedIn = true) {
    if (loggedIn) {
        $('#loginForm').hide();
        $('#userinfoViewer').show();
        $('#loginOutText').html('Logged In (<b>' + window.sessionStorage.username + '</b>)');
    } else {
        $('#userinfoViewer').hide();
        $('#loginForm').show();
        $('#loginOutText').text("Log In");
        $('#modifyDatasetButtonGroup').hide();
        $('#addNewDatasetForm').hide();
        $('.dynamic-metadata-button').hide();
    }
}