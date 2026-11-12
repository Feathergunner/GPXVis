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
		format: value => value,
		colwidth: "15ch"
	},
	{
		dataKey: "elevation_gain",
		sortKey: "elevation_gain",
		label: "Elevation Gain",
		dataSuffix: " m",
		compare: (a, b) => a - b,
		format: value => value.toFixed(0),
		colwidth: "20ch"
	},
	{
		dataKey: "elevation_delta",
		sortKey: "elevation_delta",
		label: "Elevation Delta",
		dataSuffix: " m",
		compare: (a, b) => a - b,
		format: value => value.toFixed(0),
		colwidth: "20ch"
	},
	{
		dataKey: "activity_name",
		sortKey: "activity_name",
		label: "Activity",
		compare: (a, b) => String(a).localeCompare(String(b)),
		format: value => value,
		styleclasses: ["leftalign"]
	},
	{
		dataKey: "date",
		sortKey: "datetime",
		label: "Date",
		compare: (a, b) => new Date(a) - new Date(b),
		format: value => value,
		colwidth: "25ch"
	},
	{
		dataKey: "athlete_name",
		sortKey: "athlete_name",
		label: "Athlete",
		compare: (a, b) => a - b,
		format: value => value,
		colwidth: "30ch",
		styleclasses: ["leftalign"]
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
	const fullTable = document.getElementById("tableRecords");
	const tableHeader = document.getElementById("tableRecordsHead");
	const tableBody = document.getElementById("tableRecordsBody");

	// Clear previous contents
	tableHeader.innerHTML = "";
	tableBody.innerHTML = "";

	// Create colgroup
	const colgroup = document.createElement("colgroup");
	// Configured columns
	tableColumns.forEach(column => {
		const col = document.createElement("col");
		if (column.colwidth) {
			col.style.width = column.colwidth;
		}
		colgroup.appendChild(col);
	});
	// Replace existing colgroup
	const oldColgroup = fullTable.querySelector("colgroup");
	if (oldColgroup) {
		oldColgroup.remove();
	}
	fullTable.prepend(colgroup);

	// data columns:
	tableColumns.forEach(column => {
		const th = document.createElement("th");
		th.classList.add("clickable")
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

		// Add configured columns
		tableColumns.forEach(column => {
			const td = document.createElement("td");
			if (column.styleclasses){
				column.styleclasses.forEach(styleclass => {
					td.classList.add(styleclass);
				});
			}
			let dataContent = column.format(values[column.dataKey]);
			if (column.dataSuffix){
				dataContent = dataContent+column.dataSuffix
			}
			td.textContent = dataContent;
			tr.appendChild(td);
		});
		tableBody.appendChild(tr);
	});
}