const { app, BrowserWindow } = require("electron");
//const fetch = require('node-fetch');

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
    },
  });

  win.loadURL("http://localhost:5000"); // Replace with your Flask app's address

  win.on("close", () => {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://localhost:5000/close", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

    /*xhr.onload = function() {
        if (this.status == 200) {
            console.log(this.responseText);
        } else {
            console.error('Request failed.');
        }
    };*/
    xhr.send();

    /*fetch('http://localhost:5000/close', { method: 'POST' })
      .catch((error) => {
        console.error("Failed to close Flask app:", error);
      });


    console.log('Window is being closed');

    setTimeout(() => {
      app.quit();
    }, 2000);  // Wait for 2 seconds before quitting*/
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
