// This file contains the api calls, as well as transform the data into html-text

var apiUrl = "http://zam024.fritz.box/api/"; // TODO switch out with real url, ideally during deployment
var allowedTypesList = [];

// return the dataset id
function getId() {
    var id = getUrlVars()["oid"];
    console.log("ID: " + id);
    return id;
}

// get option-html string from typename suffix
function getTypeHTMLString(name) {
    return '<li><a class="dropdown-item" href="?type=' + name + '">' + name + '</a></li>';
}

// get tableentry-html for a dataset
function getDatasetHTMLString(dataset) {
    return '<tr><th scope="row">'+ dataset[0] + '</th><td><a href="?type=' + getType() + "&oid=" + dataset[1] + '">' + dataset[1] + '</a></td></tr>'
}

/*
get html for table entry with a proeprty
The value field is editable, but the edit is blocked by default
authenticated users should be able to edit and submit
*/ 
function getPropertyHTMLString(property, value) {
    return '<tr><th scope="row">' + property + '</th><td><input class="form-control" type="text" value="' + value + '" readonly></td></tr>';
}

// XMLHttpRequest EVENTLISTENER: if a dropdown-menu (a <ul> element) with the dropdownOptions id is present, update it with the available types
function setTypeData() {
    console.log("GET " + this.responseUrl + ": " + this.responseText);
    var types = JSON.parse(this.responseText);
    allowedTypesList = [];
    // types is now a list of {name : url} elements, where url starts with a slash, and is relative to the root
    var keyName = "";
    types.forEach(element => {
        keyName = Object.keys(element)[0];
        console.log("Detected location type: " + keyName);
        allowedTypesList.push(keyName);
        $('#dropdownOptions').append(getTypeHTMLString(keyName));
    });
}

// XMLHttpRequest EVENTLISTENER: append to the list of datasets
function setDatasetList() {
    console.log("GET " + this.responseUrl + ": " + this.responseText);
    var datasets = JSON.parse(this.responseText);
    datasets.forEach(element => {
        console.log("Found Dataset: " + element)
        $('#datasetTableBody').append(getDatasetHTMLString(element));
    });
}

// XMLHttpRequest EVENTLISTENER: show dataset in table
function setDatasetView() {
    console.log("GET " + this.responseUrl + ": " + this.responseText);
    var dataset = JSON.parse(this.responseText);
    if (this.status >= 300) {
        alert(getId() + " does not exists for this storage type!");
        window.location.href = "?type=" + getType();
        return;
    }
    // dataset has a name and url attribute, as well as a map as metadata attribute
    // first, hide the list table and make the element viewer visible
    $('#datasetListTable').hide();
    $('#storageTypeChooser').hide();
    $('#datasetViewTable').show();

    // now append name and url to the view
    $('#datasetViewTableBody').append(getPropertyHTMLString('Name', dataset.name));
    $('#datasetViewTableBody').append(getPropertyHTMLString('OID', getId()));
    $('#datasetViewTableBody').append(getPropertyHTMLString('URL', dataset.url));
    
    // insert a linebreak that announces other metadata
    $('#datasetViewTableBody').append('<tr><th class="info" scope="row" colspan="2">Other Metadata</th></tr>');

    // iterate over metadata map and add additional properties
    for (const [key, val] of Object.entries(dataset.metadata)) {
        $('#datasetViewTableBody').append(getPropertyHTMLString(key, val));
    }
}

// get available types from api, put them in the relevant dropdown (via listener)
function getTypes() {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setTypeData);
    xmlhttp.open("GET", apiUrl);
    xmlhttp.send();
}

// get listing of datasets of the given type, put them in the list element (via listener)
function listDatasets(datatype) {
    var fullUrl = apiUrl + datatype;
    console.log("Full url for listing request is " + fullUrl)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setDatasetList);
    xmlhttp.open("GET", fullUrl);
    xmlhttp.send();
}

// get details about given dataset, put them in the view element (via listener)
function showDataset(datatype, dataset_id) {
    var fullUrl = apiUrl + datatype + "/" + dataset_id;
    console.log("Full url for showing request is " + fullUrl)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setDatasetView);
    xmlhttp.open("GET", fullUrl);
    xmlhttp.send();
}





//either enable the dataset listing or enable the single dataset view
async function showListingOrSingleDataset() {
    while (allowedTypesList.length == 0) {
        await new Promise(resolve => setTimeout(resolve, 10));
    }
    if (!getType() ||!allowedTypesList.includes(getType())) {
        // no type or invalid type: reload page with first allowed type TODO add some alert?
        window.location.href = "?type=" + allowedTypesList[0];
    }
    if (!getId()) { // no id given, so list all elements
        listDatasets(getType());
    } else { // an id is given, show the dataset, error message if invalid
        showDataset(getType(), getId());
    }
}


// TODO function(s) to POST new Dataset (get bearer token from auth.js)
// TODO function(s) to PUT existing Dataset (get bearer token from auth.js)
// TODO function(s) to DELETE existing Dataset (get bearer token from auth.js)