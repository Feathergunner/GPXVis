let plotType = "Lineplot";
let dimX = null;
let dimY = null;
let axisDimSelectionParent = null

function createDimSelectionForm(axis){
	axisDimSelectionParent = document.getElementById("divAxis_"+axis);
	// Clear existing selection content:
	axisDimSelectionParent.innerHTML = "";

	let axisOptionsLineplot = Object.values(axisspecs).filter(element => element.spacial_cont === true);
	let axisOptionsScatterplot = Object.values(axisspecs).filter(element => element.spacial_cat === true);
	let axisOptionsColor = null;
	if (plotType == "Lineplot"){
		// all options for coloring:
		axisOptionsColor = Object.values(axisspecs).filter(element => element.color_cont === true || element.color_cat === true);
	}
	if (plotType == "Scatterplot"){
		// only categorical data dimensions for colors:
		if (dimX !== null && (axisspecs[dimX].datasource == "ACTIVITY" || axisspecs[dimX].datasource == "ACTIVITY_DTO")
			&& (dimY !== null && (axisspecs[dimY].datasource == "ACTIVITY" || axisspecs[dimY].datasource == "ACTIVITY_DTO"))) {
			// x- and y- axis both are activity-based values, so only activity-based values are possible for colors:
			axisOptionsColor = Object.values(axisspecs).filter(element => element.label == "singular" || (element.spacial_cat === true && (element.color_cont === true || element.color_cat === true)
																		 && (element.datasource == "ACTIVITY" || element.datasource == "ACTIVITY_DTO")));
		} else {
			// any valid color option:
			axisOptionsColor = Object.values(axisspecs).filter(element => element.label == "singular" || (element.spacial_cat === true && (element.color_cont === true || element.color_cat === true)));
		}
	}

	// set which set of options is displayed:
	if (axis == "c"){
		axisOptions = axisOptionsColor
		//create Label:
		label = document.createElement("h3");
		label.textContent = "Set data source for color:";
		axisDimSelectionParent.appendChild(label);
	}else{
		// options depend on plotType:
		if (plotType == "Lineplot"){
			// datapoint-wise data:
			axisOptions = axisOptionsLineplot;
		}
		if (plotType == "Scatterplot"){
			// split-wise / activity-wise aggregated data:
			axisOptions = axisOptionsScatterplot;
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
	axisOptionsNode = Object.values(axisOptions).filter(element => element.datasource == "PATHNODE");
	axisOptionSplit = Object.values(axisOptions).filter(element => element.datasource == "SPLIT");
	axisOptionActivity = Object.values(axisOptions).filter(element => element.datasource == "ACTIVITY");
	axisOptionActivityMeta = Object.values(axisOptions).filter(element => element.datasource == "ACTIVITY_DTO");
	if (axisOptionsNode.length > 0){
		if (axisOptionSplit.length + axisOptionActivity.length + axisOptionActivityMeta.length > 0){
			label = document.createElement("h4");
			label.textContent = "Continuous data:";
			axisDimSelectionParent.appendChild(label);
		}
		axisOptionsNode.forEach(dimOption =>{
			createAxisOptionElements(dimOption, axis, newForm);
		});
	}
	if (axisOptionSplit.length > 0){
		label = document.createElement("h4");
		label.textContent = "Split-wise aggregated data:";
		newForm.appendChild(label);
		axisOptionSplit.forEach(dimOption =>{
			createAxisOptionElements(dimOption, axis, newForm);
		});
	}
	if (axisOptionActivity.length > 0){
		label = document.createElement("h4");
		label.textContent = "Activity-wise aggregated data:";
		newForm.appendChild(label);
		axisOptionActivity.forEach(dimOption =>{
			createAxisOptionElements(dimOption, axis, newForm);
		});
	}
	if (axisOptionActivityMeta.length > 0){
		label = document.createElement("h4");
		label.textContent = "Activity metadata:";
		newForm.appendChild(label);
		axisOptionActivityMeta.forEach(dimOption =>{
			createAxisOptionElements(dimOption, axis, newForm);
		});
	}

	axisDimSelectionParent.appendChild(newForm);
}

function createAxisOptionElements(dimOption, axis, htmlParent){
	//console.log(dimOption)
	const optionRadio = document.createElement("input");
	optionRadio.id = "radio_key_"+axis+"_"+dimOption.id;
	optionRadio.type = "radio";
	optionRadio.value = dimOption.id;
	optionRadio.name = "key_"+axis;
	if (axis === "x"){
		optionRadio.checked = dimOption.id == dimX;
	} else if (axis === "y"){
		optionRadio.checked = dimOption.id == dimY;
	}
	const optionLabel = document.createElement("label");
	let label = dimOption.label;
	if (dimOption.unit.length > 0){
		label = label+ " ("+dimOption.unit+")"
	}
	optionLabel.textContent = label;
	htmlParent.appendChild(optionRadio);
	htmlParent.appendChild(optionLabel);
	htmlParent.appendChild(document.createElement("br"));
}

function updatePlotType(){
	plotType = plotTypeSelect.value;
	updateDimSelectionForms();
}

function updateDimSelectionForms(){
	createDimSelectionForm("x");
	createDimSelectionForm("y");
	createDimSelectionForm("c");

}

// Initialize the page
document.addEventListener("DOMContentLoaded", function() {
	/*
	// Register event listeners
	plotTypeSelect = document.getElementById("select_plottype");
	plotTypeSelect.addEventListener("change", updatePlotType);
	*/
	//console.log(axisspecs);

	plotTypeSelect = document.getElementById("select_plottype");
	// initialize page:
	updatePlotType();
});


document.addEventListener("change", function(event) {
	if (event.target.id == "select_plottype"){
		updatePlotType();
	}
	if (event.target.type === "radio"){
		const form = event.target.closest("form");
		if (form.id == "form_select_axis_x"){
			dimX = event.target.value;
			updateDimSelectionForms();
		}
		if (form.id == "form_select_axis_y"){
			dimY = event.target.value;
			updateDimSelectionForms();
		}
	}
});