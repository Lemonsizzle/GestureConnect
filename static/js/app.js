window.onload = function () {};

window.onunload = function() {
  alert("The page is being unloaded.");

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/close", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  /*xhr.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var response = JSON.parse(this.responseText);
      alert(response.message);
    }
  };*/

  xhr.send("data=" + "unloaded");
};


function changePage(page) {
  window.location.href = page;
}

function showTab(index) {
  var buttons = document.querySelectorAll(".tab-button");
  var panes = document.querySelectorAll(".tab-pane");

  for (var i = 0; i < buttons.length; i++) {
    buttons[i].classList.remove("active");
    panes[i].classList.remove("active");
  }

  buttons[index].classList.add("active");
  panes[index].classList.add("active");
}

function getCameraSources() {
  if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
    navigator.mediaDevices
      .enumerateDevices()
      .then(function (devices) {
        var videoDevices = [];
        devices.forEach(function (device) {
          if (device.kind === "videoinput") {
            videoDevices.push({
              deviceId: device.deviceId,
              label: device.label,
            });
          }
        });
        console.log(videoDevices);
      })
      .catch(function (err) {
        console.error("Error accessing media devices.", err);
      });
  }
}

function undo() {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/db/undo", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  /*xhr.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var response = JSON.parse(this.responseText);
      alert(response.message);
    }
  };*/

  xhr.send();
}

function remove(btn) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/db/remove", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  /*xhr.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var response = JSON.parse(this.responseText);
      alert(response.message);
    }
  };*/

  xhr.send("shape=" + btn);

  // Assuming there is an element in your HTML like this: <div id="myElement">Hello</div>
  var element = document.getElementById(btn);
  if (element) {
    element.remove();
  }
}

function record(btn) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/db/record", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  /*xhr.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var response = JSON.parse(this.responseText);
      alert(response.message);
    }
  };*/

  xhr.send("shape=" + btn);
}

function functionSelected(choice) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/submit", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  /*xhr.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var response = JSON.parse(this.responseText);
      alert(response.message);
    }
  };*/
  xhr.send("choice=" + choice);
}

function tabClosed() {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/close", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  /* xhr.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var response = JSON.parse(this.responseText);
            alert(response.message);
        }
    }; */
  xhr.send("message=Tab closed");
}

function postData() {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/interact", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  /*xhr.onload = function() {
        if (this.status == 200) {
            console.log(this.responseText);
        } else {
            console.error('Request failed.');
        }
    };*/

  // Get form data
  var fps = document.getElementById("fps").checked ? "on" : "off";
  var hflip = document.getElementById("hflip").checked ? "on" : "off";
  var vflip = document.getElementById("vflip").checked ? "on" : "off";

  var formData = "fps=" + fps + "&hflip=" + hflip + "&vflip=" + vflip;
  xhr.send(formData);
}

function changeSource() {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/change_source", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  xhr.onload = function () {
    if (this.status == 200) {
      console.log(this.responseText);
      var videoElement = document.getElementById("live");
      videoElement.src = "/video_feed?" + new Date().getTime();
    } else {
      console.error("Request failed.");
    }
  };

  // Get form data
  var src = document.getElementById("cam_src").value;

  console.log(src);

  if (src === "") {
    console.log("Invalid Source");
    return;
  }

  var formData = "src=" + src;
  xhr.send(formData);
}

function test() {
  getCameraSources();
}
