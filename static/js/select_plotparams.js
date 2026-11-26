let plotType = "Lineplot"
//let keyX = axisdim_cont[0]
//let keyY = axisdim_cont[1]
//let keyC = axisdim_color[0]

let axisDimSelectionParent = null

function createDimSelectionForm(axis){
	axisDimSelectionParent = document.getElementById("divAxis_"+axis);
	// Clear existing selection content:
	axisDimSelectionParent.innerHTML = "";

	let axisOptions = null

	// set which set of options is displayed:
	if (axis == "c"){
		// options are possible data sources for color:
		axisOptions = Object.values(axisspecs).filter(element => element.color_cat === true);
		//create Label:
		label = document.createElement("h3");
		label.textContent = "Set data source for color:";
		axisDimSelectionParent.appendChild(label);
	}else{
		// options depend on plotType:
		if (plotType == "Lineplot"){
			// datapoint-wise data:
			axisOptions = Object.values(axisspecs).filter(element => element.spacial_cont === true);

		}
		if (plotType == "Scatterplot"){
			// activity-wise / aggregated data:
			axisOptions = Object.values(axisspecs).filter(element => element.spacial_cat === true);
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
		optionRadio.value = dimOption.id;
		optionRadio.name = "key_"+axis;
		const optionLabel = document.createElement("label");
		let label = dimOption.label;
		if (dimOption.unit.length > 0){
			label = label+ " ("+dimOption.unit+")"
		}
		optionLabel.textContent = label;
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