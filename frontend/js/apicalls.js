// This file contains the api calls, as well as transform the data into html-text
var apiUrl = "http://zam024.fritz.box/api/"; // TODO switch out with real url, ideally during deployment
var allowedTypesList = [];

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
    return type
}

// set the text of the typetext element 
function setTypeText() {
    $('#typetext').text(getType())
}

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
function getPropertyHTMLString(property, value, readonly=true) {
    return '<tr><th scope="row">' + property + '</th><td><input class="form-control" type="text" value="' + value + (readonly ? '" readonly' : '"') + '></td></tr>';
}

/*
* Fill given table with data from given dataset
* if readonly is false, make all but OID editable
* else everything is readonly
*/
function fillDatasetTable(table, dataset, readonly=faltruese) {
    // now append name and url to the view
    table.append(getPropertyHTMLString('Name', dataset.name, readonly));
    table.append(getPropertyHTMLString('OID', getId()));
    table.append(getPropertyHTMLString('URL', dataset.url, readonly));

    // insert a linebreak that announces other metadata
    table.append('<tr><th class="info" scope="row" colspan="2">Other Metadata</th></tr>');

    // iterate over metadata map and add additional properties
    for (const [key, val] of Object.entries(dataset.metadata)) {
        table.append(getPropertyHTMLString(key, val, editable));
    }
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

// XMLHttpRequest EVENTLISTENER: show banner with new dataset id
function showNewDatasetID() {
    console.log("POST " + this.responseUrl + ": " + this.responseText);
    var data = JSON.parse(this.responseText);
    var id = data[0];
    var alertHTML = '<div class="alert alert-success" role="alert">Dataset created! OID is: <a href="?type=' + getType() + '&oid=' + id + '">' + id + '</a></div>';
    $('#storageTypeChooser').after(alertHTML);
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
    if (window.sessionStorage.auth_token) {
        $('#modifyDatasetButtonGroup').show();
    }

    fillDatasetTable($('#datasetViewTableBody'), dataset, true);
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
        if (window.sessionStorage.auth_token) {
            $('#addNewDatasetButton').show();
        }
        listDatasets(getType());
    } else if (getId() == "new") {
        alert ("Do stuff for new dataset i.e. edit datset with empty oid");
    } else { // an id is given, show the dataset, error message if invalid
        showDataset(getType(), getId());
    }
}


// POST new Dataset (get bearer token from session storage)
function createNewDataset(datatype, name, url, metadata) {
    var dataset = {"name" : name, "url" : url, "metadata" : metadata};
    var fullUrl = apiUrl + datatype;
    console.log("Full url for creating new dataset is " + fullUrl)
    console.log("New Dataset is " + dataset)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", showNewDatasetID);
    xmlhttp.open("POST", fullUrl);
    xmlhttp.setRequestHeader('Authorization', 'Bearer ' + window.sessionStorage.auth_token);
    xmlhttp.setRequestHeader('Content-Type', 'application/json');
    xmlhttp.send(JSON.stringify(dataset));
    // TODO disable all buttons, put a spinner on save
}

// TODO function(s) to PUT existing Dataset (get bearer token from session storage)
// TODO function(s) to DELETE existing Dataset (get bearer token from session storage)