// References to html elements:
let activityTypeSelect = null;
let recordTypeSelect = null;
let rowLimitSetter = null;

// Current sorting configuration
let sortColumn = "time_hms";
let sortAscending = true;

const tableColumns = [
	{
		dataKey: "time_hms",
		sortKey: "time",
		label: "Time",
		compare: (a, b) => a - b,
        format: value => value
	},
	{
		dataKey: "elevation_gain",
		sortKey: "elevation_gain",
		label: "Elevation Gain (m)",
		compare: (a, b) => a - b,
        format: value => value.toFixed(0)
	},
	{
		dataKey: "elevation_delta",
		sortKey: "elevation_delta",
		label: "Elevation Delta (m)",
		compare: (a, b) => a - b,
        format: value => value.toFixed(0)
	},
	{
		dataKey: "athlete_name",
		sortKey: "athlete_name",
		label: "Athlete",
		compare: (a, b) => a - b,
        format: value => value
	},
	{
		dataKey: "date",
		sortKey: "datetime",
		label: "Date",
		compare: (a, b) => new Date(a) - new Date(b),
        format: value => value
	}
];

// Initialize the page
document.addEventListener("DOMContentLoaded", function() {
	// setup html elements:
	activityTypeSelect = document.getElementById("activitytype_select");
	recordTypeSelect = document.getElementById("recordtype_select");
	rowLimitSetter = document.getElementById("rowLimitSetter");

	// Register event listeners
	activityTypeSelect.addEventListener("change", updateRecordTypeSelect);
	recordTypeSelect.addEventListener("change", renderTable);
	rowLimitSetter.addEventListener("change", renderTable);

	// Initial rendering
    //let currentActivityType = "running"
    //let currentRecordType = recordtypes[currentActivityType][0];

	updateRecordTypeSelect();
});

// Update recordTypeSelect for the selected activity:
function updateRecordTypeSelect(){
	currentActivityType = activityTypeSelect.value;
	const recordTypes = recordtypes[currentActivityType];

	// Clear existing selection content
	recordTypeSelect.innerHTML = "";
	// Create new options
	recordTypes.forEach(rt => {
		const new_option = document.createElement("option");
		new_option.value = rt;
		new_option.textContent = rt;
		recordTypeSelect.appendChild(new_option);
	});
	currentRecordType = recordtypes[currentActivityType][0]
	renderTable()
}

// Main function: renders the table
function renderTable() {
	const currentActivityType = activityTypeSelect.value
	const currentRecordType = recordTypeSelect.value;
	const rowLimit = rowLimitSetter.value;
	const selectedData = Object.values(recorddata[currentActivityType][currentRecordType]);
	const tableHeader = document.getElementById("tableRecordsHead");
	const tableBody = document.getElementById("tableRecordsBody");

	// Clear previous contents
	tableHeader.innerHTML = "";
	tableBody.innerHTML = "";

	tableColumns.forEach(column => {
		const th = document.createElement("th");
		th.textContent = column.label;
		// Sorting indicator
		if (sortColumn === column.dataKey) {
			th.textContent += sortAscending ? " ▲" : " ▼";
		}
		// Sorting functionality
		th.addEventListener("click", function() {
			if (sortColumn === column.dataKey) {
				sortAscending = !sortAscending;
			} else {
				sortColumn = column.dataKey;
				sortAscending = true;
			}
			renderTable();
		});
		tableHeader.appendChild(th);
	});

	// Convert dictionary into array
	let rows = Object.entries(selectedData);
	// Apply sorting
	if (sortColumn !== null) {
		const column = tableColumns.find(
			col => col.dataKey === sortColumn
		);
		rows.sort((a, b) => {
			const valueA = a[1][column.sortKey];
			const valueB = b[1][column.sortKey];
			const comparison = column.compare(valueA, valueB);
			return sortAscending ? comparison : -comparison;
		});
	}

	// Apply row limit
	rows = rows.slice(0, rowLimit);

	// Generate table contents
	rows.forEach(([name, values]) => {
		const tr = document.createElement("tr");
		// Add item name
		//const nameCell = document.createElement("td");
		//nameCell.textContent = name;
		//tr.appendChild(nameCell);

		// Add configured columns
		tableColumns.forEach(column => {
			const td = document.createElement("td");
			td.textContent = column.format(values[column.dataKey]);
			tr.appendChild(td);
		});
		tableBody.appendChild(tr);
	});
}