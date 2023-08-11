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

function populateClasses() {
  // todo: populate buttons in second tab-pane based on database class (and another for new classes)
  // todo: add ids to the tab-panes

  // Generate buttons for recording macros
  /*classes = self.db.getClasses()
  rowlen = 4
  buttons = []
  for idx, c in enumerate(classes):
      b = Button(class_buttons, text=c, command=lambda: self.record(c.lower()))
      b.grid(row=idx//rowlen, column=idx%rowlen, sticky=W)
      buttons.append(b)*/
}

function record(btn) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/record", true);
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

window.addEventListener("beforeunload", function (e) {
  tabClosed();
});

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

  if (src == "") {
    console.log("Invalid Source");
    return;
  }

  var formData = "src=" + src;
  xhr.send(formData);
}

function test() {
  getCameraSources();
  return;
}
