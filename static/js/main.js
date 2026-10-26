
let latitude;
let longitude;
let mapzoom = 8;
let map;
let range = 5;

function get_from_selection(selectionFieldName){
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
		get_from_selection("athlete_id")[0]
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

async function get_activities(considergps=false, addcheckbox=false, defaultchecked=false) {
	/*
	Get a set of activities from the database.

	Gets a rendered html-table containing the activity-metadata from the server.
	*/
	const response = await fetch("/api/get_activities_table", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			athlete_ids: get_from_selection("athlete_id"),
			type_ids: get_from_selection("type_id"),
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

async function runMapPlotter() {
	/*
	Initiates the RouteGraphPlotter
	*/
	var selected_activity_ids = get_from_selection("activity_id");

	const range = document.getElementById("range").value;
	const response = await fetch("/api/runMapPlotter", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: selected_activity_ids,
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
	var selected_activity_ids = get_from_selection("activity_id");
	console.log(selected_activity_ids);

	const response = await fetch("/api/runTourAnimation", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: selected_activity_ids,
			mapzoom: mapzoom,
			filename: document.getElementById("input_filename").value
		})
	});
	monitorProgress();
}

async function runDataPlotter() {
	/*
	Initiates the RouteProfilePlotter
	*/
	var selected_activity_ids = get_from_selection("activity_id");
	console.log(selected_activity_ids)

	var form_axis_x = document.getElementById("form_select_axis_x");
	const axis_x = form_axis_x.elements["radio_axis_x"].value;
	var form_axis_y= document.getElementById("form_select_axis_y");
	const axis_y = form_axis_y.elements["radio_axis_y"].value;

	const response = await fetch("/api/runDataPlotter", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_ids: selected_activity_ids,
			date_min: document.getElementById("inputDateMin").value,
			date_max: document.getElementById("inputDateMax").value,
			use_unkown_date: document.getElementById("checkUnknownDate").checked,
			axis_x: axis_x,
			axis_y: axis_y,
			filename: document.getElementById("input_filename").value
		})
	});
	monitorProgress();
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


function initializeMap(){
	/*
	Handles the map tool for GPS location selection.
	*/
	// open map
	map = L.map("map").setView([52.52, 13.405],mapzoom);

	// OpenStreetMap Layer
	L.tileLayer(
		"https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
		{
			attribution: "&copy; OpenStreetMap contributors"
		}
	).addTo(map);

	let marker = null;

	// handle mouse click on map
	map.on("click", function(event) {
		const lat = event.latlng.lat;
		const lng = event.latlng.lng;
		latitude = lat
		longitude = lng
		// remove existing marker
		if (marker !== null) {
			map.removeLayer(marker);
		}
		// add new marker
		marker = L.marker([lat, lng]).addTo(map);
		// get coordinates:
		document.getElementById("coords").innerText = "Starting position: " + `Lat: ${lat.toFixed(5)}, ` + `Lng: ${lng.toFixed(5)}`;
		console.log(lat, lng);
	});
	map.on("zoom", function(event) {
		const zoom = map.getZoom();
		mapzoom = zoom;
		document.getElementById("zoom").value = mapzoom;
	})
}

function on_zoom_input_change(zoom){
	map.setZoom(zoom);
}

document.addEventListener("DOMContentLoaded", () => {
	const mapdiv = document.getElementById("map");
	if (mapdiv) {
		initializeMap()
	}
	const date_range_max_selector = document.getElementById("inputDateMax");
	if (date_range_max_selector) {
		date_range_max_selector.value = new Date().toISOString().slice(0, 10);
	}
});