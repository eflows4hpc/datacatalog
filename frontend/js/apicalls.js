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
    return id;
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

// get option-html string from typename suffix
function getTypeHTMLString(name) {
    return '<li><a class="dropdown-item" href="?type=' + name + '">' + name + '</a></li>';
}

// get tableentry-html for a dataset
function getDatasetHTMLString(dataset) {
    var safename = escapeHtml(dataset[0]);
    return '<tr><th scope="row">'+ safename + '</th><td><a href="?type=' + getType() + "&oid=" + dataset[1] + '">' + dataset[1] + '</a></td></tr>'
}

/*
get html for table entry with a property
The value field is editable, but the edit is blocked by default
authenticated users should be able to edit and submit
*/ 
function getPropertyHTMLString(property, value, readonly=true) {
    var safekey = escapeHtml(property);
    var safeval = escapeHtml(value);
    return '<tr><th scope="row">' + safekey + '</th><td colspan="2"><input class="form-control" type="text" id="' + safekey + 'Input" value="' + safeval + (readonly ? '" readonly' : '"') + '></td></tr>';
}

/*
* Create a short random id. This is used for mapping metadata properties with their value fields, as they are dynamically provided (and can theoretically be as little or as many as possible)
*/
function getRandomID() {
    return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(2);
}

function removeMetadataRow(id) {
    $('#' + id + 'Row').remove();
}

/*
get html for table entry with a proeprty that is part of the metadata
The key and value fields are editable, but the edit is blocked by default
authenticated users should be able to edit and submit
*/ 
function getMetadataPropertyHTMLString(property, value, readonly=true) {
    var randID = getRandomID();
    var safekey = escapeHtml(property);
    var safeval = escapeHtml(value);
    return '<tr id="' + randID + 'Row"><th scope="row"><input class="form-control dynamic-metadata" type="text" id="' + randID + '" value="' + safekey + (readonly ? '" readonly' : '"') + '></th><td><input class="form-control" type="text" id="' + randID + 'Input" value="' + safeval + (readonly ? '" readonly' : '"') + '></td><th><button type="button" class="btn btn-danger dynamic-metadata-button" onclick="removeMetadataRow(\'' + randID + '\')" id="' + randID + 'Button">-</button></th></tr>';
}

/**
 * collect metadata from any present metadata inputs. If none are there, return an empty dict.
 */
function collectMetadata() {
    var metadata = {};
    $('.dynamic-metadata').each( function() {
        var id = this.id;
        var key = $(this).val();
        var selector = '#' + id + 'Input';
        var value = $(selector).val();
        metadata[key] = value;
    });
    return metadata;
}

function addMetadataRow(table, key, value, readonly=true) {
    table.append(getMetadataPropertyHTMLString(key, value, readonly));
}

/*
* Fill given table with data from given dataset
* if readonly is false, make all but OID editable
* else everything is readonly
*/
function fillDatasetTable(table, dataset, readonly=true, id=getId()) {
    // now append name and url to the view
    table.append(getPropertyHTMLString('Name', dataset.name, readonly));
    table.append(getPropertyHTMLString('OID', id));
    table.append(getPropertyHTMLString('URL', dataset.url, readonly));

    // insert a linebreak that announces other metadata
    table.append('<tr class="table-info"><th scope="row" colspan="2">Other Metadata</th><th><button type="button" class="btn btn-success" onclick="addMetadataRow($(\'#datasetViewTableBody\'), \'property\', \'value\', false)" id="addMetadataButton">+</button></th></tr>');

    // iterate over metadata map and add additional properties
    for (const [key, val] of Object.entries(dataset.metadata)) {
        addMetadataRow(table, key, val, readonly);
    }
    $('#addMetadataButton').hide();
    $('.dynamic-metadata-button').hide();
}

// XMLHttpRequest EVENTLISTENER: if a dropdown-menu (a <ul> element) with the dropdownOptions id is present, update it with the available types
function setTypeData() {
    console.log("Response to list available types GET: " + this.responseText);
    var types = JSON.parse(this.responseText);
    allowedTypesList = [];
    // types is now a list of {name : url} elements, where url starts with a slash, and is relative to the root
    var keyName = "";
    types.forEach(element => {
        keyName = Object.keys(element)[0];
        console.debug("Detected location type: " + keyName);
        allowedTypesList.push(keyName);
        $('#dropdownOptions').append(getTypeHTMLString(keyName));
    });
}

// XMLHttpRequest EVENTLISTENER: append to the list of datasets
function setDatasetList() {
    console.log("Response to list datasets GET: " + this.responseText);
    var datasets = JSON.parse(this.responseText);
    datasets.forEach(element => {
        console.debug("Found Dataset: " + element)
        $('#datasetTableBody').append(getDatasetHTMLString(element));
    });
}

// XMLHttpRequest EVENTLISTENER: show banner with new dataset id
function showNewDatasetID() {
    console.log("Response to create new Dataset POST: " + this.responseText);
    if (this.status >= 400) {
        // some error occured while getting the data
        // show an alert and don't do anything else
        var alertHTML = '<div class="alert alert-danger" role="alert">Invalid response from server! Either the API server is down, or the dataset creation failed. Response code: ' + this.status + '<hr>Please try agagin later, and if the error persists, contact the server administrator.</div>';
        $('#storageTypeChooser').after(alertHTML);
        return;
    }
    var data = JSON.parse(this.responseText);
    var id = data[0];
    var alertHTML = '<div class="alert alert-success" role="alert">Dataset created! OID is: <a href="?type=' + getType() + '&oid=' + id + '">' + id + '</a></div>';
    $('#storageTypeChooser').after(alertHTML);
    $('#spinner').remove();
}

// XMLHttpRequest EVENTLISTENER: show banner with success message for change
function showSuccessfullyChangedDataset() {
    console.log("Response to modify dataset PUT: " + this.responseText);
    if (this.status >= 400) {
        // some error occured while getting the data
        // show an alert and don't do anything else
        var alertHTML = '<div class="alert alert-danger" role="alert">Invalid response from server! Either the API server is down, or the dataset modification failed. Response code: ' + this.status + '<hr>Please try agagin later, and if the error persists, contact the server administrator.</div>';
        $('#storageTypeChooser').after(alertHTML);
        return;
    }
    var alertHTML = '<div class="alert alert-success" role="alert">Dataset was successfully changed!</div>';
    $('#storageTypeChooser').after(alertHTML);
    $('#spinner').remove();
}

// XMLHttpRequest EVENTLISTENER: show banner with success message for deletion
function showSuccessfullyDeletedDataset() {
    console.log("Response to DELETE dataset: " + this.responseText);
    if (this.status >= 400) {
        // some error occured while getting the data
        // show an alert and don't do anything else
        var alertHTML = '<div class="alert alert-danger" role="alert">Invalid response from server! Either the API server is down, or the dataset deletion failed. Response code: ' + this.status + '<hr>Please try agagin later, and if the error persists, contact the server administrator.</div>';
        $('#storageTypeChooser').after(alertHTML);
        return;
    }
    var alertHTML = '<div class="alert alert-danger" role="alert">Dataset was successfully deleted!</div>';
    $('#storageTypeChooser').after(alertHTML);
    $('#spinner').remove();
}

// XMLHttpRequest EVENTLISTENER: show dataset in table
async function setDatasetView() {
    console.log("Response to show dataset GET: " + this.responseText);
    var dataset = JSON.parse(this.responseText);
    if (this.status >= 300) {
        var alertHTML = '<div class="alert alert-danger" role="alert">Invalid id was requested. Redirecting to list of elements with the same type.<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div>';
        $('#storageTypeChooser').before(alertHTML);
        await new Promise(resolve => setTimeout(resolve, 3000));
        window.location.href = "?type=" + getType();
        return;
    }
    // dataset has a name and url attribute, as well as a map as metadata attribute
    // first, hide the list table and make the element viewer visible
    $('#datasetListTable').hide();
    $('#storageTypeChooser').hide();
    $('#datasetViewTable').show();
    $('#modifyDatasetButtonGroup').hide();
    if (window.sessionStorage.auth_token) {
        $('#modifyDatasetButtonGroup').show();
    }

    fillDatasetTable($('#datasetViewTableBody'), dataset, true);
    enableButtons(false, true, true);
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
    console.log("Sending GET request to  " + fullUrl + " for listing datasets.")
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", setDatasetList);
    xmlhttp.open("GET", fullUrl);
    xmlhttp.send();
}

// get details about given dataset, put them in the view element (via listener)
function showDataset(datatype, dataset_id) {
    var fullUrl = apiUrl + datatype + "/" + dataset_id;
    console.log("Sending GET request to  " + fullUrl + " for showing dataset.")
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
    if (!getType() || !allowedTypesList.includes(getType())) {
        if (getType) {
            // an invalid type was provided, give some alert
            var alertHTML = '<div class="alert alert-danger" role="alert">Invalid type was requested. Redirecting to default type.<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div>';
            $('#storageTypeChooser').before(alertHTML);
            await new Promise(resolve => setTimeout(resolve, 3000));
        }
        window.location.href = "?type=" + allowedTypesList[0];
    }
    if (!getId()) { // no id given, so list all elements
        if (window.sessionStorage.auth_token) {
            $('#addNewDatasetButton').show();
        }
        listDatasets(getType());
    } else if (getId() == "new") {
        $('#datasetListTable').hide();
        $('#storageTypeChooser').hide();
        $('#datasetViewTable').show();

        $('#modifyDatasetButtonGroup').hide();
        $('#addMetadataButton').hide();
        $('.dynamic-metadata-button').hide();
    
        fillDatasetTable($('#datasetViewTableBody'), {"name" : "", "url" : "", "metadata" : {}}, false, "");
        if (window.sessionStorage.auth_token) {
            $('#modifyDatasetButtonGroup').show();
            $('#addMetadataButton').show();
            $('.dynamic-metadata-button').show();
        }
        enableButtons(true, false, true);
    } else { // an id is given, show the dataset, error message if invalid
        showDataset(getType(), getId());
    }
}

// POST new Dataset (get bearer token from session storage)
function createNewDataset(datatype, name, url, metadata) {
    var dataset = {"name" : name, "url" : url, "metadata" : metadata};
    var fullUrl = apiUrl + datatype;
    console.log("Sending POST request to  " + fullUrl + " for creating dataset.")
    console.debug("New Dataset is " + dataset)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", showNewDatasetID);
    xmlhttp.open("POST", fullUrl);
    xmlhttp.setRequestHeader('Authorization', 'Bearer ' + window.sessionStorage.auth_token);
    xmlhttp.setRequestHeader('Content-Type', 'application/json');
    xmlhttp.send(JSON.stringify(dataset));
    enableButtons(false, false, false);
    $('#button-save').prepend('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="spinner"></span>');
    disableMetadataButtons();
}

// PUT existing Dataset (get bearer token from session storage)
function updateDataset(oid, datatype, name, url, metadata) {
    var dataset = {"name" : name, "url" : url, "metadata" : metadata};
    var fullUrl = apiUrl + datatype + "/" + oid;
    console.log("Sending PUT request to  " + fullUrl + " for editing dataset.")
    console.debug("New Dataset data is " + dataset)
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", showSuccessfullyChangedDataset);
    xmlhttp.open("PUT", fullUrl);
    xmlhttp.setRequestHeader('Authorization', 'Bearer ' + window.sessionStorage.auth_token);
    xmlhttp.setRequestHeader('Content-Type', 'application/json');
    xmlhttp.send(JSON.stringify(dataset));
    enableButtons(false, false, false);
    $('#button-save').prepend('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="spinner"></span>');
    disableMetadataButtons();
}

// DELETE existing Dataset (get bearer token from session storage)
function deleteDataset(oid, datatype) {
    var fullUrl = apiUrl + datatype + "/" + oid;
    console.log("Sending DELETE request to  " + fullUrl + " for deleting dataset.")
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.addEventListener("loadend", showSuccessfullyDeletedDataset);
    xmlhttp.open("DELETE", fullUrl);
    xmlhttp.setRequestHeader('Authorization', 'Bearer ' + window.sessionStorage.auth_token);
    xmlhttp.send();
    enableButtons(false, false, false);
    $('#button-delete').prepend('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="spinner"></span>');
    disableMetadataButtons();
}

function editButtonPressed() {
    // make all inputfields editable, enable save button, disable edit button
    enableButtons(true, false, true);
    // unset readonly for metadata inputs
    $('.dynamic-metadata').each( function() {
        var id = this.id;
        var selector = '#' + id + 'Input';
        $(this).attr("readonly", false)
        $(selector).attr("readonly", false);
    });

    // unset readonly for name and url
    $('#NameInput').attr("readonly", false);
    $('#URLInput').attr("readonly", false);

    // show add/remove metadata row buttons
    $('#addMetadataButton').show();
    $('.dynamic-metadata-button').show();
}

function deleteButtonPressed() {
    var datatype = getType();
    var id = getId();

    if (id == "new") {
        // no need to delete anything, just redirect to the list after confirmation
        if (confirm("Discard new " + datatype+ "?")) {
            window.location.replace("?type=" + datatype);
        }
        return;
    }

    if (confirm("Delete " + datatype +  " with the id " + id + "?")) {
        deleteDataset(id, datatype);
    }

    // success is handled by the xmlhttp event listener
}

function saveButtonPressed() {
    // if id is '"new"', post a new one, else update the existing one
    
    var datatype = getType();
    var id = getId();
    var name = $('#NameInput').val();
    var url = $('#URLInput').val();
    var metadata = collectMetadata();

    if (id == "new") {
        // if user does not confirm, don't do anything
        if (confirm("Save new " + datatype+ "?")) {
            createNewDataset(datatype, name, url, metadata);
        }
        return;
    }

    if (confirm("Save changes to " + datatype +  " with the id " + id + "?")) {
        updateDataset(id, datatype, name, url, metadata);
    }
    // success is handled by the xmlhttp event listener
}

function enableButtons(save, edit, del) {
    $('#button-save').attr('disabled', !save);
    $('#button-edit').attr('disabled', !edit);
    $('#button-delete').attr('disabled', !del);
}

function disableMetadataButtons() {
    $('#addMetadataButton').attr('disabled', true);
    $('.dynamic-metadata-button').attr('disabled', true);
}