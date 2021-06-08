// This file will contain the api calls, as well as transform the data into html-text (via a template)

var apiUrl = "http://zam024.fritz.box/api/";

// get variable map from url
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
    var type = getUrlVars()["type"];
    console.log("Type: " + type);
    return type;
}

// return the dataset id
function getId() {
    var id = getUrlVars()["id"];
    console.log("ID: " + id);
    return id;
}

// set the text of the typetext element 
function setTypeText() {
    $('#typetext').text(getType());
}

// get option-html string from typename and url suffix
function getTypeHTMLString(name) {
    return '<li><a class="dropdown-item" href="?type=' + name + '">' + name + '</a></li>';
}

// XMLHttpRequest EVENTLISTENER: if a dropdown-menu (a <ul> element) with the dropdownOptions id is present, update it with the available types
function setTypeData() {
    console.log("GET " + this.responseUrl + ": " + this.responseText);
    var types = JSON.parse(this.responseText);
    // types is now a list of {name : url} elements, where url starts with a slash, and is relative to the root
    var keyName = "";
    types.forEach(element => {
        keyName = Object.keys(element)[0];
        console.log("Detected location type: " + keyName);
        $('#dropdownOptions').append(getTypeHTMLString(keyName));
    });
}

// XMLHttpRequest EVENTLISTENER: append to the list of datasets
function setDatasetList() {
    console.log("GET " + this.responseUrl + ": " + this.responseText);
    var datasets = JSON.parse(this.responseText);

}

// XMLHttpRequest EVENTLISTENER: show single datset
function setDatasetList() {
    console.log("GET " + this.responseUrl + ": " + this.responseText);
    var datasets = JSON.parse(this.responseText);

}

// get available types from api, put them in the relevant dropdown
function getTypes() {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setTypeData);
    xmlhttp.open("GET", apiUrl);
    xmlhttp.send();
}

// get listing of datasets of the given type, put them in the list element
function listDatasets(datatype) {
    var fullUrl = apiUrl + datatype;
    console.log("Full url for listing request is " + fullUrl)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setDatasetList);
    xmlhttp.open("GET", fullUrl);
    xmlhttp.send();
}

// get details about given dataset, put them in the view element§
function showDataset(datatype, dataset_id) {
    var fullUrl = apiUrl + datatype + "/" + dataset_id;
    console.log("Full url for showing request is " + fullUrl)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setDatasetView);
    xmlhttp.open("GET", fullUrl);
    xmlhttp.send();
}





//either enable the dataset listing or enable the single dataset view
function showListingOrSingleDataset() {
    // compare getType with allowed types
    // if none or illegal type: show first allowed one
    // then check if dataset id is present, if yes, show that dataset
    // if no id, or non-existent id, list all sets of type
}