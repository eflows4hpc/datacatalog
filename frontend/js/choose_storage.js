// get data from url query variables
function getUrlVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

// return the storage type
function getType() {
    var type = getUrlVars()["type"]
    console.log("Type: " + type)
    return type
}

// set the text of the typetext element 
function setTypeText() {
    $('#typetext').text(getType())
}