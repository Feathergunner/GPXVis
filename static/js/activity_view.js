let currentActivityIndex = null;

const dataTableRows = [
	{
		dataKey: "date",
		label: "Date",
		format: value => value
	},
	{
		dataKey: "time",
		label: "Time",
		format: value => value
	},
	{
		dataKey: "distance_km",
		label: "Total Distance",
		format: value => value
	},
	{
		dataKey: "duration_hms",
		label: "Total Duration",
		format: value => value
	},
	{
		dataKey: "elevation",
		label: "Total Elevation Gain (m)",
		format: value => value
	},
	{
		dataKey: "pace",
		label: "Average Pace (min/km)",
		format: value => value
	},
	{
		dataKey: "speed",
		label: "Average Speed (km/h)",
		format: value => value
	},
	{
		dataKey: "startpos_str",
		label: "GPS Location (lat,lon)",
		format: value => value
	}
]

function get_previous_activity(){
	if (currentActivityIndex > 0)
	{
		currentActivityIndex -= 1;
		getActivityData();
	}
}

function get_next_activity(){
	if (currentActivityIndex < activity_ids.length-1)
	{
		currentActivityIndex += 1;
		getActivityData();
	}
}

async function getActivityData(){
	const response = await fetch("/api/get_activity_and_records_by_activity_id", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			activity_id: activity_ids[currentActivityIndex]
		})
	});
	const data = await response.json();
	if (data != null){
		updateActivity(data);	
	}
}

function updateActivity(data){
	activityData = data["activity"];
	recordsData = data["records"];

	// update Header:
	const header = document.getElementById("activityHeader");
	header.innerHTML = "";
	header.textContent = activityData["name"]+" ("+activityData["type_name"]+") by "+activityData["athlete_name"];
	// fill data table:
	const tableData = document.getElementById("activityDataTable");
	tableData.innerHTML = "";
	dataTableRows.forEach(row => {
		const tr = document.createElement("tr");
		const tdLabel = document.createElement("td");
		tdLabel.textContent = row.label;
		tdLabel.classList.add("leftalign");
		tr.appendChild(tdLabel);
		const tdContent = document.createElement("td");
		tdContent.textContent = activityData[row.dataKey];
		tr.appendChild(tdContent);
		tableData.appendChild(tr);
	});
	// fill records table:
	const tableRecords = document.getElementById("activityRecordsTable");
	tableRecords.innerHTML = "";

	const tableHeader = document.createElement("thead")
	const thLabel = document.createElement("th");
	thLabel.classList.add("leftalign");
	thLabel.textContent = "Category";
	tableHeader.appendChild(thLabel);
	const thTime = document.createElement("th");
	thTime.textContent = "Time";
	tableHeader.appendChild(thTime);
	tableRecords.appendChild(tableHeader);

	recordsData.forEach(record => {
		const tr = document.createElement("tr");
		const tdRecordLabel = document.createElement("td");
		tdRecordLabel.textContent = record.rtype_name+" ("+record.rtype_distance+" km)";
		tdRecordLabel.classList.add("leftalign");
		tr.appendChild(tdRecordLabel);
		const tdRecordTime = document.createElement("td");
		tdRecordTime.textContent = record.time_hms;
		tr.appendChild(tdRecordTime);
		tableRecords.appendChild(tr);
	});

	// add preview image:
}

document.addEventListener("DOMContentLoaded", () => {
	currentActivityIndex = activity_ids.length-1;
	// get activity data:
	getActivityData();
});