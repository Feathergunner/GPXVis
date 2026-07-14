
let latitude;
let longitude;
let mapzoom = 8
let map;

function openTab(evt, tabName) {
	// Declare all variables
	var i, tabcontent, tablinks;

	// Get all elements with class="tabcontent" and hide them
	tabcontent = document.getElementsByClassName("tabcontent");
	//console.log(tabcontent)
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].style.display = "none";
	}

	// Get all elements with class="tablinks" and remove the class "active"
	tablinks = document.getElementsByClassName("tablinks");
	for (i = 0; i < tablinks.length; i++) {
		tablinks[i].className = tablinks[i].className.replace(" active", "");
	}

	// Show the current tab, and add an "active" class to the button that opened the tab
	//console.log(tabName)
	elements_to_show = document.getElementsByClassName(tabName)
	//console.log(elements_to_show)
	for (i = 0; i < elements_to_show.length; i++) {
		elements_to_show[i].style.display = "block";
	}
	
	evt.currentTarget.className += " active";
} 

async function loadFolders() {
	// API aufrufen
	const response = await fetch("/api/list-dir");
	// JSON lesen
	const data = await response.json();
	// Container holen
	const container = document.getElementById("folderlist");
	//console.log(container)

	// Add content:
	container.innerHTML = "";
	data.folders.forEach(folder => {
		const label = document.createElement("label");
		// radio button:
		const checkb = document.createElement("input");
		checkb.type = "checkbox";
		checkb.name = "selectedFolder";
		checkb.id = "checkbox_dir";
		checkb.value = folder;
		label.appendChild(checkb);
		label.appendChild( document.createTextNode(folder));
		label.appendChild(document.createElement("br"));
		container.appendChild(label);
	});
}

async function newDataDir(){
	const dirNameInput = document.getElementById("input_dirname")
	const response = await fetch("/api/newDir", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			dirName: dirNameInput.value
		})
	});
	loadFolders();
}

function getSelectedFolders(){
	var dirform = document.getElementById("form_select_dir");
	const dir = dirform.elements["checkbox_dir"].value;
	const selected_dirs = [];
	const checkboxes = document.querySelectorAll('input[name="selectedFolder"]:checked');
	checkboxes.forEach(cb => {
		selected_dirs.push(cb.value);
	});
	return selected_dirs
}

async function uploadFiles(){
	const formData = new FormData();
	// uploaded files:
	const input = document.getElementById("fileInput");
	for (const file of input.files) {
		formData.append(
			"files",
			file
		);
	}
	// target directory:
	const selected_dirs = getSelectedFolders()
	const targetFolder = selected_dirs[0]
	formData.append(
		"target_folder",
		targetFolder
	);

	const response = await fetch(
		"/api/uploadGPX",{
			method: "POST",
			body: formData
		}
	);
}

async function loadDatabase(){
	const response = await fetch("/api/list_files");
	const data = await response.json();
	//console.log(data);
	createFileTable(data);
}

async function rebuildDatabase(){
	const response = await fetch("/api/rebuild_database");
	loadDatabase()
}

function createFileTable(data) {
	const container =
		document.getElementById(
			"div_database"
		);
	container.innerHTML = "";
	const table = document.createElement("table");
	table.classList.add("file-table");

	//--------------------------------------------------
	// Header
	//--------------------------------------------------
	const header = document.createElement("tr");
	const th_cb_folder = document.createElement("th");
	th_cb_folder.className = "checkbox-column";
	header.appendChild(th_cb_folder);
	const th_folder = document.createElement("th");
	th_folder.textContent = "Directory"
	header.appendChild(th_folder);
	const th_cb_file = document.createElement("th");
	th_cb_file.className = "checkbox-column";
	header.appendChild(th_cb_file);
	[
		"File",
		"Date",
		"Total Distance",
		"Total Time",
		"Total Elevation"
	].forEach(text => {
		const th = document.createElement("th");
		th.textContent = text;
		header.appendChild(th);
	});

	table.appendChild(header);

	//--------------------------------------------------
	// Zeilen
	//--------------------------------------------------
	data.all_folders.forEach(folder => {

		const files = data.all_files[folder] || [];
		files.forEach((file, index) => {
			const row = document.createElement("tr");

			//------------------------------------------
			// Ordner-Checkbox
			//------------------------------------------

			const folderCheckboxCell = document.createElement("td");
			if (index === 0) {
				const cb = document.createElement("input");
				cb.type = "checkbox";
				cb.className = "folder-checkbox checkbox-column";
				cb.dataset.folder = folder;
				folderCheckboxCell.appendChild(cb);
			}
			row.appendChild(folderCheckboxCell);

			//------------------------------------------
			// Ordnername
			//------------------------------------------

			const folderCell = document.createElement("td");
			if (index === 0) {
				folderCell.textContent = folder;
			}
			row.appendChild(folderCell);

			//------------------------------------------
			// Datei-Checkbox
			//------------------------------------------
			const fileCheckboxCell = document.createElement("td");
			const fileCb = document.createElement("input");
			fileCb.type = "checkbox";
			fileCb.className = "file-checkbox checkbox-column";
			fileCb.dataset.folder = folder;
			fileCb.dataset.file = file;
			fileCheckboxCell.appendChild(fileCb);
			row.appendChild(fileCheckboxCell);

			//------------------------------------------
			// Dateiname
			//------------------------------------------
			const fileCell = document.createElement("td");
			fileCell.textContent = file;
			row.appendChild(fileCell);

			//------------------------------------------
			// Dummy-Metadaten
			//------------------------------------------
			const cell_date = document.createElement("td");
			cell_date.textContent = "Date";
			row.appendChild(cell_date);
			const cell_dist = document.createElement("td");
			cell_dist.textContent = "Meta A";
			row.appendChild(cell_dist);
			const cell_time = document.createElement("td");
			cell_time.textContent = "Meta B";
			row.appendChild(cell_time);
			const cell_ele = document.createElement("td");
			cell_ele.textContent = "Meta C";
			row.appendChild(cell_ele);
			table.appendChild(row);
		});
	});
	container.appendChild(table);
}

async function runMapPlotter() {
	var typeform = document.getElementById("form_select_type");
	const type = typeform.elements["radio_type"].value;

	const selected_dirs = getSelectedFolders()
	console.log(selected_dirs)

	const range = document.getElementById("range").value;
	const response = await fetch("/api/runMapPlotter", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			lat: latitude,
			lon: longitude,
			mapzoom: mapzoom,
			range: range,
			type: type,
			use_unkown_type: document.getElementById("checkUnknownType").checked,
			dir: selected_dirs,
			date_min: document.getElementById("inputDateMin").value,
			date_max: document.getElementById("inputDateMax").value,
			use_unkown_date: document.getElementById("checkUnknownDate").checked,
			filename: document.getElementById("input_filename_map").value
		})
	});
	//console.log("started computation...")
	monitorProgress();
}

async function runDataPlotter() {
	var typeform = document.getElementById("form_select_type");
	const type = typeform.elements["radio_type"].value;

	const selected_dirs = getSelectedFolders()
	//console.log(selected_dirs)

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
			type: type,
			use_unkown_type: document.getElementById("checkUnknownType").checked,
			dir: selected_dirs,
			date_min: document.getElementById("inputDateMin").value,
			date_max: document.getElementById("inputDateMax").value,
			use_unkown_date: document.getElementById("checkUnknownDate").checked,
			axis_x: axis_x,
			axis_y: axis_y,
			filename: document.getElementById("input_filename_plot").value
		})
	});
	//console.log("started computation...")
	monitorProgress();
}

function monitorProgress() {
	//console.log("Monitor Progress")
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
	//console.log("Display progress:")
	//console.log(data)
	const progress = data.total_progress;
	// UI aktualisieren
	document.getElementById("progressBar").value = progress*100;
	document.getElementById("progressText").textContent = "Current step: " + data.current_task + " - " + (progress*100).toFixed(2) + "%";	
}

async function openResultImage(){
	const response = await fetch("/api/getResultPath");
	const data = await response.json();
	console.log(data)
	if (data.result_filename != "unknown" && data.result_filename != null){
		window.open(data.result_filename, '_blank');
	}
}


function initializeMap(){
	// Karte erzeugen
	map = L.map("map").setView([52.52, 13.405],mapzoom);

	// OpenStreetMap Layer
	L.tileLayer(
		"https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
		{
			attribution: "&copy; OpenStreetMap contributors"
		}
	).addTo(map);

	// Marker Variable
	let marker = null;

	// Klick auf Karte
	map.on("click", function(event) {
		const lat = event.latlng.lat;
		const lng = event.latlng.lng;
		latitude = lat
		longitude = lng
		// Alten Marker entfernen
		if (marker !== null) {
			map.removeLayer(marker);
		}

		// Neuen Marker setzen
		marker = L.marker([lat, lng]).addTo(map);

		// Koordinaten anzeigen
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

document.addEventListener(
	"DOMContentLoaded",
	() => {
		initializeMap();
		loadFolders();
		loadDatabase();
		// Initial tab selection:
		document.getElementById("button_tab_howto").click()
		inputDateMax.value = new Date().toISOString().slice(0, 10);
	}
);