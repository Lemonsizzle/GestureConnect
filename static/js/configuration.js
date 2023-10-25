window.onload = function () {
  fetch("/load")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      // Handle the data from the backend
      console.log(data);
      populateItems(data);
    })
    .catch((error) => {
      console.error("There was a problem with the fetch operation:", error);
    });
};

window.onunload = function () {
  alert("The page is being unloaded.");

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/close", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  xhr.send("data=" + "unloaded");
};

function populateItems(data) {
  const scriptInfo = [];
  function recursiveParse(node, handedness) {
    for (const gesture in node) {
      if (node.hasOwnProperty(gesture)) {
        for (const direction in node[gesture]) {
          if (node[gesture].hasOwnProperty(direction)) {
            const scripts = node[gesture][direction];
            for (const script of scripts) {
              scriptInfo.push({
                handedness,
                gesture,
                direction,
                script,
              });
            }
          }
        }
      }
    }
  }

  for (const handedness in data["config"]) {
    if (data["config"].hasOwnProperty(handedness)) {
      const node = data["config"][handedness];
      recursiveParse(node, handedness);
    }
  }

  console.log(scriptInfo);

  scriptInfo.forEach((item) => {
    addItem(
      item.handedness,
      item.gesture,
      item.direction,
      item.script,
      data["classes"],
      data["scripts"],
    );
    console.log(item);
  });
}

var backendActions = [];
var backendScripts = [];

function addItem(
  handedness = "",
  action = "",
  direction = "",
  script = "",
  actions = null,
  scripts = null,
) {
  const newItem = document.createElement("div");

  const itemsDiv = document.querySelector("#" + handedness + "_items");

  const n = itemsDiv.children.length - 1;

  //if (!handedness.length || !action.length || !direction.length || !script.length) return;
  console.log(backendActions);
  if (actions != null) backendActions = actions;
  if (scripts != null) backendScripts = scripts;

  newItem.className = "item";
  newItem.id = handedness + "_item" + n;
  newItem.innerHTML = `
      <!-- Dropdown for gesture -->
      <label for="${handedness}_action${n}">Gesture:</label>
      <select id="${handedness}_action${n}" class="dropdown">
      </select>
      
      <br />
    
      <!-- Radio buttons for direction -->
      <label for="${handedness}_up${n}">Up</label>
      <input type="radio" id="${handedness}_up${n}" name="${handedness}_direction${n}" value="up" />
      
      <label for="${handedness}_down${n}">Down</label>
      <input type="radio" id="${handedness}_down${n}" name="${handedness}_direction${n}" value="down" />
      
      <label for="${handedness}_left${n}">Left</label>
      <input type="radio" id="${handedness}_left${n}" name="${handedness}_direction${n}" value="left" />
      
      <label for="${handedness}_right${n}">Right</label>
      <input type="radio" id="${handedness}_right${n}" name="${handedness}_direction${n}" value="right" />
    
      <br />
      
      <!-- Dropdown for script -->    
      <label for="${handedness}_script${n}">Script:</label>
      <select id="${handedness}_script${n}" class="dropdown">
      </select>
  `;

  console.log(newItem);
  itemsDiv.insertBefore(newItem, itemsDiv.lastElementChild);

  const actionSelector = document.getElementById(`${handedness}_action${n}`);
  if (actionSelector && backendActions !== []) {
    for (let j = 0; j < backendActions.length; j++) {
      // Create a new option element
      const newOption = document.createElement("option");

      // Set the value and text of the new option
      newOption.value = backendActions[j];
      newOption.textContent = backendActions[j];

      // Append the new option to the select
      actionSelector.appendChild(newOption);
    }

    actionSelector.value = action;
  }

  const directionRadio = document.getElementById(
    handedness + "_" + direction + n,
  );
  if (directionRadio && direction !== "") directionRadio.checked = 1;

  const scriptSelector = document.getElementById(`${handedness}_script${n}`);
  if (scriptSelector && backendScripts !== []) {
    for (let j = 0; j < backendScripts.length; j++) {
      // Create a new option element
      const newOption = document.createElement("option");

      // Set the value and text of the new option
      newOption.value = backendScripts[j];
      newOption.textContent = backendScripts[j];

      // Append the new option to the select
      scriptSelector.appendChild(newOption);
    }

    scriptSelector.value = script;
  }
}

function save() {
  var jsonData = {};

  // Loop through all items
  const items = document.querySelectorAll(".item");
  items.forEach((item, index) => {
    // Get handedness
    var handedness = item.parentElement.getAttribute("id").split("_")[0];
    let id = item.getAttribute("id");
    let number = id.charAt(id.length - 1);

    // Loop through checkboxes for fingers within this item
    var action = "";
    const actionDropdown = document.getElementById(
      `${handedness}_action${number}`,
    );
    if (actionDropdown) action = actionDropdown.value;

    if (action === "") return;

    // Get selected radio button for direction within this item
    var direction = "";
    const directionRadio = item.querySelector(
      `input[name="${handedness}_direction${number}"]:checked`,
    );
    if (directionRadio) direction = directionRadio.value;

    if (direction === "") return;

    if (!jsonData[handedness][action][direction]) {
      jsonData[handedness][action][direction] = [];
    }

    // Get selected radio button for direction within this item
    const scriptDropdown = document.getElementById(`${handedness}_script${number}`);
    if (scriptDropdown) {
      if (scriptDropdown.value === "") return;
      jsonData[handedness][action][direction].push(scriptDropdown.value);
    }
    console.log(jsonData);
  });

  // Convert to JSON string
  const jsonString = JSON.stringify(jsonData);

  // You can now use or save jsonString as needed
  console.log(jsonString);

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/save", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  xhr.send("config=" + jsonString);
}
