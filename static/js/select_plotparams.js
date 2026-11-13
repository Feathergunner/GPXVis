let plotType = "Lineplot"
let keyX = axisdim_cont[0]
let keyY = axisdim_cont[1]
let keyC = axisdim_color[0]

let axisDimSelectionParent = null

function createDimSelectionForm(axis){
	axisDimSelectionParent = document.getElementById("divAxis_"+axis);
	// Clear existing selection content:
	axisDimSelectionParent.innerHTML = "";

	// set which set of options is displayed:
	if (axis == "c"){
		// options are possible data sources for color:
		axisOptions = axisdim_color;
		//create Label:
		label = document.createElement("h3");
		label.textContent = "Set data source for color:";
		axisDimSelectionParent.appendChild(label);
	}else{
		// options depend on plotType:
		if (plotType == "Lineplot"){
			// datapoint-wise data:
			axisOptions = axisdim_cont;
		}
		if (plotType == "Scatterplot"){
			// activity-wise / aggregated data:
			axisOptions = axisdim_cat;
		}
		//create Label:
		label = document.createElement("h3");
		label.textContent = "Set dimension of "+axis+"-axis:";
		axisDimSelectionParent.appendChild(label);
	}

	// create form:
	const newForm = document.createElement("form");
	newForm.id = "form_select_axis_"+axis;
	// create options:
	axisOptions.forEach(dimOption =>{
		const optionRadio = document.createElement("input");
		optionRadio.type = "radio";
		optionRadio.value = dimOption.value;
		optionRadio.name = "key_"+axis;
		const optionLabel = document.createElement("label");
		optionLabel.textContent = dimOption.label;
		newForm.appendChild(optionRadio);
		newForm.appendChild(optionLabel);
		newForm.appendChild(document.createElement("br"));
	});
	axisDimSelectionParent.appendChild(newForm);
}

function updatePlotType(){
	console.log("updatePlotType")
	plotType = plotTypeSelect.value;
	// create selection forms, depending on plotType
	createDimSelectionForm("x");
	createDimSelectionForm("y");
	createDimSelectionForm("c");
}

// Initialize the page
document.addEventListener("DOMContentLoaded", function() {
	// setup html elements:
	plotTypeSelect = document.getElementById("select_plottype");

	// Register event listeners
	plotTypeSelect.addEventListener("change", updatePlotType);

	updatePlotType();
});