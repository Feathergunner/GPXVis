let latitude = -1;
let longitude = -1;
let mapzoom = 8;
let map = null;
let range = 5;

let current_marker = null;

async function initializeMap(){
	/*
	Handles the map tool for GPS location selection.
	*/
	// ask for default map setting parameters:
	const response = await fetch("/api/get_default_map_parameter");
	const data = await response.json();
	default_lat = data.default_latitude;
	default_lon = data.default_longitude;
	// set default map position
	// if no default, focus map on berlin:
	if (default_lat > 0){
		latitude = default_lat;
	}else{
		latitude = 52.516;
	}
	if (default_lon > 0){
		longitude = default_lon;
	}else{
		longitude = 13.38;
	}
	document.getElementById("inputLatitude").value = latitude;
	document.getElementById("inputLongitude").value = longitude;

	// open map
	map = L.map("map").setView([latitude, longitude],mapzoom);
	if (default_lat > 0 && default_lon > 0){
		// also place a marker:
		current_marker = setMarkerOnMap(latitude, longitude);
	}

	// OpenStreetMap Layer
	L.tileLayer(
		"https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
		{
			attribution: "&copy; OpenStreetMap contributors"
		}
	).addTo(map);

	// handle mouse click on map
	map.on("click", function(event) {
		const lat = event.latlng.lat;
		const lng = event.latlng.lng;
		latitude = lat;
		longitude = lng;
		current_marker = setMarkerOnMap(lat, lng);
	});
	map.on("zoom", function(event) {
		const zoom = map.getZoom();
		mapzoom = zoom;
		document.getElementById("zoom").value = mapzoom;
	})
}

function setMarkerOnMap(lat, lng, updateInput=false){
	// remove existing marker
	if (current_marker !== null) {
		map.removeLayer(current_marker);
	}
	// add new marker
	current_marker = L.marker([lat, lng]).addTo(map);
	// update text label:
	//document.getElementById("coords").innerText = "Starting position: " + `Lat: ${lat.toFixed(5)}, ` + `Lng: ${lng.toFixed(5)}`;
	if (updateInput){
		document.getElementById("inputLatitude").value = lat;
		document.getElementById("inputLongitude").value = lon;
	}
	return current_marker
}

function onZoomInputChange(zoom){
	map.setZoom(zoom);
}

function updateLatLon(){
	latitude = document.getElementById("inputLatitude").value;
	longitude = document.getElementById("inputLongitude").value;
	map.panTo(new L.LatLng(latitude, longitude));
	setMarkerOnMap(latitude, longitude, false);
}

document.addEventListener("DOMContentLoaded", () => {
	// initialize map:
	const mapdiv = document.getElementById("map");
	if (mapdiv) {
		initializeMap();
	}
});