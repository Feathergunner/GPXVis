
function getFromSelection(selectionFieldName){
	/*
	get list of values from a set of checkboxes
	*/
	const selection = [];
	const checkboxes = document.querySelectorAll('input[name='+selectionFieldName+']:checked');
	checkboxes.forEach(cb => {
		selection.push(cb.value);
	});
	return selection
}

async function addAthlete(){
	/*
	Add an athlete to the database
	*/
	const response = await fetch("/api/add_athlete", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			name: document.getElementById("input_athletename").value
		})
	});
	location.reload();
}

async function uploadFiles(){
	/*
	Add activities to the database.

	User 'uploads' a set of gpx-files.
	These files are parsed into activities which are in turn added to the database.
	The files are also copied to a local folder for future reference.
	*/

	const formData = new FormData();
	// add selected athlete:
	formData.append(
		"athlete_id",
		getFromSelection("athlete_id")[0]
	);
	// add uploaded files:
	const input = document.getElementById("fileInput");
	for (const file of input.files) {
		formData.append(
			"files",
			file
		);
	}
	const response = await fetch(
		"/api/uploadGPX",{
			method: "POST",
			body: formData
		}
	);
}

async function getActivities(considergps=false, addcheckbox=false, defaultchecked=false) {
	/*
	Get a set of activities from the database.

	Gets a rendered html-table containing the activity-metadata from the server.
	*/

	if (considergps){
		range = document.getElementById("activity_range_selection").value;
	} else{
		range = 0;
	}

	const response = await fetch("/api/get_activities_table", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			athlete_ids: getFromSelection("athlete_id"),
			type_ids: getFromSelection("type_id"),
			date_min: document.getElementById("inputDateMin").value,
			date_max: document.getElementById("inputDateMax").value,
			use_unkown_date: document.getElementById("checkUnknownDate").checked,
			lat: latitude,
			lon: longitude,
			range: range,
			consider_gps: considergps,
			add_checkbox: addcheckbox,
			default_checked: defaultchecked
		})
	})
    if (!response.ok) {
        console.error("Failed to update label");
        return;
    }
    const html = await response.text();
    document.getElementById("activity_table").outerHTML = html;
}

async function deleteAthletes() {
	const response = await fetch("api/delete_athletes", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			athlete_ids: getFromSelection("athlete_id")
		})
	});
	location.reload();
}

async function deleteTypes() {
	const response = await fetch("api/delete_types", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_type_ids: getFromSelection("type_id")
		})
	});
	location.reload();
}

async function deleteActivities() {
	const response = await fetch("api/delete_activities", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: getFromSelection("cb_activity_id")
		})
	});
}

async function renameActivities() {
	const response = await fetch("/api/rename_activities", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: getFromSelection("cb_activity_id"),
			new_name: document.getElementById("input_activityname").value
		})
	});
}

async function runMapPlotter() {
	/*
	Initiates the RouteGraphPlotter
	*/

	const response = await fetch("/api/runMapPlotter", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: getFromSelection("cb_activity_id"),
			lat: latitude,
			lon: longitude,
			mapzoom: mapzoom,
			filename: document.getElementById("input_filename").value
		})
	});
	monitorProgress();
}

async function runTourPlotter() {
	/*
	Initiates the TourGraphPlotter
	*/
	const response = await fetch("/api/runTourAnimation", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: getFromSelection("cb_activity_id"),
			mapzoom: mapzoom,
			animation_speedup: document.getElementById("input_animation_speedup").value,
			animation_fps: document.getElementById("input_animation_fps").value,
			animation_zoom_in: document.getElementById("input_animation_zoom").checked,
			color_key: document.getElementById("form_select_color_key").elements["color_key"].value,
			filename: document.getElementById("input_filename").value
		})
	});
	monitorProgress();
}

async function runDataPlotter() {
	/*
	Initiates the RouteProfilePlotter
	*/
	const response = await fetch("/api/runDataPlotter", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: getFromSelection("cb_activity_id"),
			date_min: document.getElementById("inputDateMin").value,
			date_max: document.getElementById("inputDateMax").value,
			use_unkown_date: document.getElementById("checkUnknownDate").checked,
			axis_x: document.getElementById("form_select_axis_x").elements["key_x"].value,
			axis_y: document.getElementById("form_select_axis_y").elements["key_y"].value,
			color_key: document.getElementById("form_select_axis_c").elements["key_c"].value,
			filename: document.getElementById("input_filename").value
		})
	});
	monitorProgress();
}

async function runDataPlotterRecords(){
	/*
	Initiates the RouteProfilePlotter for record data
	*/
	const response = await fetch("/api/runRecordPlotter", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			recorddata_ids: getFromSelection("selectedRecords"),
			axis_x: document.getElementById("form_select_axis_x").elements["key_x"].value,
			axis_y: document.getElementById("form_select_axis_y").elements["key_y"].value,
			color_key: document.getElementById("form_select_axis_c").elements["key_c"].value,
			filename: document.getElementById("input_filename").value
		})
	});
	monitorProgress();
}

function selectAllActivities(select=true) {
	checkboxes = document.getElementsByName('cb_activity_id');
 	for(var checkbox in checkboxes){
		checkboxes[checkbox].checked = select;
 	}
}

async function createRecordCategory(){
	const response = await fetch("/api/create_record_category", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			recordActivityType: getFromSelection("type_id"),
			recordName: document.getElementById("input_new_record_name").value,
			recordDistance: document.getElementById("input_new_record_distance").value
		})
	});
}

function monitorProgress() {
	/*
	Gets progress-updates during server tasks
	*/
	const interval = setInterval(
		async () => {
			const response = await fetch("/api/progress");
			const data = await response.json();
			console.log("progress:")
			console.log(data)
			if (data.total_progress >= 1) {
				clearInterval(interval);
				openResultImage();
			}
			else if (data.current_status == "stopped" || data.current_status == "finished"){
				clearInterval(interval);
			}
			displayProgress(data)	
		},
		500
	);
}

function displayProgress(data){
	/*
	Displays the computation progress during server tasks.
	*/
	const progress = data.total_progress;
	// scale the UI
	document.getElementById("progressBar").value = progress*100;
	document.getElementById("progressText").textContent = "Current step: " + data.current_task + " - " + (progress*100).toFixed(2) + "%";	
}

async function openResultImage(){
	/*
	Opens an image in a new tab.
	*/
	const response = await fetch("/api/getResultPath");
	const data = await response.json();
	console.log(data)
	if (data.result_filename != "unknown" && data.result_filename != null){
		window.open(data.result_filename, '_blank');
	}
}

async function setDefaultSettings(){
	const response = await fetch("/api/update_settings", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			athlete_ids: getFromSelection("athlete_id"),
			type_ids: getFromSelection("type_id"),
			lat: latitude,
			lon: longitude
		})
	});
}

document.addEventListener("DOMContentLoaded", () => {
	//const mapdiv = document.getElementById("map");
	//if (mapdiv) {
	//	initializeMap()
	//}
	const date_range_max_selector = document.getElementById("inputDateMax");
	if (date_range_max_selector) {
		var maxDate = new Date();
		maxDate.setDate(maxDate.getDate() + 1);
		//date_range_max_selector.value = new Date().toISOString().slice(0, 10);
		date_range_max_selector.value = maxDate.toISOString().slice(0, 10);
	}
});