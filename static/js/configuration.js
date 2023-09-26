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
  function recursiveParse(node, key) {
    for (const direction in node) {
      if (node.hasOwnProperty(direction)) {
        const scripts = node[direction];
        for (const script of scripts) {
          scriptInfo.push({
            key,
            direction,
            script,
          });
        }
      }
    }
  }

  for (const key in data["config"]) {
    if (data["config"].hasOwnProperty(key)) {
      const node = data["config"][key];
      recursiveParse(node, key);
    }
  }

  scriptInfo.forEach((item) => {
    addItem(item.key, item.direction, item.script, data["classes"], data["scripts"]);
    console.log(item);
  });
}

function addItem(action= "", direction= "", script= "", actions= [], scripts= []) {
  const newItem = document.createElement("div");

  const itemsDiv = document.querySelector("#items");

  const n = itemsDiv.children.length - 1;

  if (!action.length || !direction.length || !script.length)
    return

  newItem.className = "item";
  newItem.id = "item" + n;
  newItem.innerHTML = `
      <!-- Check boxes for fingers -->
      <!--
      <label for="thumb${n}">Thumb</label>
      <input type="checkbox" id="thumb${n}" name="fingers${n}" value="thumb" />
      
      <label for="index${n}">Index</label>
      <input type="checkbox" id="index${n}" name="fingers${n}" value="index" />
      
      <label for="middle${n}">Middle</label>
      <input type="checkbox" id="middle${n}" name="fingers${n}" value="middle" />
      
      <label for="ring${n}">Ring</label>
      <input type="checkbox" id="ring${n}" name="fingers${n}" value="ring" />
      
      <label for="pinky${n}">Pinky</label>
      <input type="checkbox" id="pinky${n}" name="fingers${n}" value="pinky" />
      -->
      
      <select id="action${n}" class="dropdown">
      </select>
      
      <br />
    
      <!-- Radio buttons for direction -->
      <label for="up${n}">Up</label>
      <input type="radio" id="up${n}" name="direction${n}" value="up" />
      
      <label for="down${n}">Down</label>
      <input type="radio" id="down${n}" name="direction${n}" value="down" />
      
      <label for="left${n}">Left</label>
      <input type="radio" id="left${n}" name="direction${n}" value="left" />
      
      <label for="right${n}">Right</label>
      <input type="radio" id="right${n}" name="direction${n}" value="right" />
    
      <br />
    
      <label for="script${n}">Script:</label>
      <select id="script${n}" class="dropdown">
      </select>
  `;

  console.log(newItem);
  itemsDiv.insertBefore(newItem, itemsDiv.lastElementChild);

  /*
  let digits = ["thumb", "index", "middle", "ring", "pinky"];

  if (keyFingers.length === digits.length) {
    for (let i = 0; i < keyFingers.length; i++) {
      const keyFinger = keyFingers[i];
      const digit = digits[i];
      if (keyFinger === "1") {
        const fingerCheck = document.getElementById(digit + n);
        fingerCheck.checked = 1;
      }
    }
  } else {
    console.log("String and array have different lengths.");
  }
  */

  const actionSelector = document.getElementById(`action${n}`);
  if (actionSelector && action !== "") {
    for (let j = 0; j < actions.length; j++) {
      // Create a new option element
      const newOption = document.createElement("option");

      // Set the value and text of the new option
      newOption.value = actions[j];
      newOption.textContent = actions[j];

      // Append the new option to the select
      actionSelector.appendChild(newOption);
    }

    actionSelector.value = action;
  }

  const directionRadio = document.getElementById(direction + n);
  if (directionRadio && direction !== "") directionRadio.checked = 1;

  const scriptSelector = document.getElementById(`script${n}`);
  if (scriptSelector && script !== "") {
    for (let j = 0; j < scripts.length; j++) {
      // Create a new option element
      const newOption = document.createElement("option");

      // Set the value and text of the new option
      newOption.value = scripts[j];
      newOption.textContent = scripts[j];

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
    // Loop through checkboxes for fingers within this item
    var fingers = "";
    const fingerCheckboxes = item.querySelectorAll(
      `input[name="fingers${index}"]`,
    );
    fingerCheckboxes.forEach((checkbox) => {
      fingers += checkbox.checked ? 1 : 0;
    });

    if (fingers === "00000") return;

    // Get selected radio button for direction within this item
    var direction = "";
    const directionRadio = item.querySelector(
      `input[name="direction${index}"]:checked`,
    );
    if (directionRadio) direction = directionRadio.value;

    if (direction === "") return;

    if (!jsonData[fingers]) {
      jsonData[fingers] = {};
      if (!jsonData[fingers][direction]) {
        jsonData[fingers][direction] = [];
      }
    }

    // Get selected radio button for direction within this item
    const scriptDropdown = item.querySelector(`input[name="script${index}"]`);
    if (scriptDropdown) {
      if (scriptDropdown.value === "") return;
      jsonData[fingers][direction].push(scriptDropdown.value);
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

function configureItem() {
  console.log();
}
