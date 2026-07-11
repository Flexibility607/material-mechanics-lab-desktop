"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("settingsAPI", {
    get: () => ipcRenderer.invoke("settings:get"),
    save: (settings) => ipcRenderer.invoke("settings:save", settings),
    close: () => ipcRenderer.send("settings:close")
});

contextBridge.exposeInMainWorld("desktopAPI", {
    saveTextFile: (options) => ipcRenderer.invoke("file:save-text", options)
});
