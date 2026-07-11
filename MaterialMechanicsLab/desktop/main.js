"use strict";

const { app, BrowserWindow, Menu, dialog, ipcMain, safeStorage, shell } = require("electron");
const childProcess = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const path = require("path");

const DEFAULT_MODEL = "gpt-5-mini";
let mainWindow = null;
let settingsWindow = null;
let serverProcess = null;
let serverPort = null;
let serverLog = null;
let quitting = false;

function settingsPath() {
    return path.join(app.getPath("userData"), "settings.json");
}

function readSettingsFile() {
    try {
        return JSON.parse(fs.readFileSync(settingsPath(), "utf8"));
    } catch {
        return {};
    }
}

function secureSettings() {
    const raw = readSettingsFile();
    let apiKey = process.env.OPENAI_API_KEY || "";
    if (!apiKey && raw.apiKeyEncrypted && safeStorage.isEncryptionAvailable()) {
        try {
            apiKey = safeStorage.decryptString(Buffer.from(raw.apiKeyEncrypted, "base64"));
        } catch {
            apiKey = "";
        }
    }
    return {
        apiKey,
        model: raw.model || process.env.OPENAI_MODEL || DEFAULT_MODEL
    };
}

function writeSettings(input) {
    const current = readSettingsFile();
    const next = {
        model: /^[A-Za-z0-9._-]+$/.test(input.model || "") ? input.model : DEFAULT_MODEL
    };
    if (input.clearKey) {
        delete next.apiKeyEncrypted;
    } else if ((input.apiKey || "").trim()) {
        if (!safeStorage.isEncryptionAvailable()) {
            throw new Error("当前系统无法安全加密 API 密钥。");
        }
        next.apiKeyEncrypted = safeStorage.encryptString(input.apiKey.trim()).toString("base64");
    } else if (current.apiKeyEncrypted) {
        next.apiKeyEncrypted = current.apiKeyEncrypted;
    }
    fs.mkdirSync(path.dirname(settingsPath()), { recursive: true });
    fs.writeFileSync(settingsPath(), JSON.stringify(next, null, 2), "utf8");
}

function serverExecutable() {
    if (app.isPackaged) {
        return path.join(process.resourcesPath, "server", "material_mechanics_server.exe");
    }
    return path.join(__dirname, "..", "server-dist", "material_mechanics_server", "material_mechanics_server.exe");
}

function reservePort() {
    return new Promise((resolve, reject) => {
        const probe = net.createServer();
        probe.once("error", reject);
        probe.listen(0, "127.0.0.1", () => {
            const port = probe.address().port;
            probe.close(() => resolve(port));
        });
    });
}

function healthCheck(port) {
    return new Promise((resolve) => {
        const request = http.get({
            hostname: "127.0.0.1",
            port,
            path: "/api/health",
            timeout: 800
        }, (response) => {
            response.resume();
            resolve(response.statusCode === 200);
        });
        request.on("timeout", () => {
            request.destroy();
            resolve(false);
        });
        request.on("error", () => resolve(false));
    });
}

async function waitForServer(port) {
    for (let attempt = 0; attempt < 120; attempt += 1) {
        if (await healthCheck(port)) return;
        await new Promise((resolve) => setTimeout(resolve, 250));
    }
    throw new Error("本地计算服务启动超时。");
}

async function startServer() {
    const executable = serverExecutable();
    if (!fs.existsSync(executable)) {
        throw new Error("未找到内置计算服务：" + executable);
    }
    serverPort = await reservePort();
    const config = secureSettings();
    const logPath = path.join(app.getPath("userData"), "server.log");
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    serverLog = fs.openSync(logPath, "a");
    const env = {
        ...process.env,
        PYTHONUTF8: "1",
        OPENAI_MODEL: config.model
    };
    if (config.apiKey) env.OPENAI_API_KEY = config.apiKey;
    serverProcess = childProcess.spawn(
        executable,
        ["--host", "127.0.0.1", "--port", String(serverPort)],
        {
            windowsHide: true,
            env,
            stdio: ["ignore", serverLog, serverLog]
        }
    );
    serverProcess.once("exit", (code) => {
        serverProcess = null;
        if (!quitting && mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send("server-exited", code);
        }
    });
    await waitForServer(serverPort);
}

function stopServer() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
    }
    if (serverLog !== null) {
        try {
            fs.closeSync(serverLog);
        } catch {
            // Log handle may already be closed by Windows.
        }
        serverLog = null;
    }
}

async function restartServer() {
    stopServer();
    await startServer();
    if (mainWindow && !mainWindow.isDestroyed()) {
        await mainWindow.loadURL("http://127.0.0.1:" + serverPort + "/combined_report.html");
    }
}

function createMenu() {
    const template = [
        {
            label: "文件",
            submenu: [
                {
                    label: "打印或导出 PDF",
                    accelerator: "Ctrl+P",
                    click: () => mainWindow && mainWindow.webContents.print()
                },
                { type: "separator" },
                { role: "quit", label: "退出" }
            ]
        },
        {
            label: "设置",
            submenu: [
                {
                    label: "OpenAI API 设置",
                    accelerator: "Ctrl+,",
                    click: openSettingsWindow
                },
                {
                    label: "重新载入",
                    accelerator: "Ctrl+R",
                    click: () => mainWindow && mainWindow.reload()
                }
            ]
        },
        {
            label: "帮助",
            submenu: [
                {
                    label: "打开运行日志",
                    click: () => shell.openPath(path.join(app.getPath("userData"), "server.log"))
                },
                {
                    label: "关于",
                    click: () => dialog.showMessageBox(mainWindow, {
                        type: "info",
                        title: "材料力学实验报告助手",
                        message: "材料力学实验报告助手",
                        detail: "七次实验原始数据计算、扫描报告模板生成、Markdown/HTML/PDF 导出与 OpenAI 轻度润色。",
                        buttons: ["确定"]
                    })
                }
            ]
        }
    ];
    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1500,
        height: 960,
        minWidth: 980,
        minHeight: 700,
        show: false,
        autoHideMenuBar: false,
        title: "材料力学实验报告助手",
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: true
        }
    });
    mainWindow.once("ready-to-show", () => mainWindow.show());
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (!url.startsWith("http://127.0.0.1:")) shell.openExternal(url);
        return { action: "deny" };
    });
    mainWindow.webContents.on("will-navigate", (event, url) => {
        if (!url.startsWith("http://127.0.0.1:")) {
            event.preventDefault();
            shell.openExternal(url);
        }
    });
    await mainWindow.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(
        "<html><body style='font-family:Segoe UI;padding:40px'><h2>正在启动材料力学计算服务…</h2></body></html>"
    ));
    try {
        await startServer();
        await mainWindow.loadURL("http://127.0.0.1:" + serverPort + "/combined_report.html");
    } catch (error) {
        await dialog.showMessageBox(mainWindow, {
            type: "error",
            title: "启动失败",
            message: "应用未能启动本地计算服务",
            detail: error.message,
            buttons: ["确定"]
        });
    }
}

function openSettingsWindow() {
    if (settingsWindow && !settingsWindow.isDestroyed()) {
        settingsWindow.focus();
        return;
    }
    settingsWindow = new BrowserWindow({
        width: 560,
        height: 470,
        parent: mainWindow,
        modal: true,
        resizable: false,
        title: "OpenAI API 设置",
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: true
        }
    });
    settingsWindow.setMenuBarVisibility(false);
    settingsWindow.loadFile(path.join(__dirname, "settings.html"));
    settingsWindow.on("closed", () => {
        settingsWindow = null;
    });
}

ipcMain.handle("settings:get", () => {
    const config = secureSettings();
    return { configured: Boolean(config.apiKey), model: config.model };
});

ipcMain.handle("settings:save", async (_event, input) => {
    writeSettings(input || {});
    await restartServer();
    return { ok: true };
});

ipcMain.handle("file:save-text", async (event, input) => {
    if (!mainWindow || event.sender.id !== mainWindow.webContents.id) {
        throw new Error("不允许从当前窗口执行导出。")
    }
    const payload = input || {};
    const content = typeof payload.content === "string" ? payload.content : "";
    if (!content || content.length > 5_000_000) {
        throw new Error("导出内容为空或超过大小限制。")
    }
    const requestedName = path.basename(String(payload.defaultName || "实验报告.md"));
    const extension = path.extname(requestedName).toLowerCase();
    if (!new Set([".md", ".html"]).has(extension)) {
        throw new Error("仅支持导出 Markdown 或 HTML 文件。")
    }

    let filePath;
    const automatedExportDir = process.env.MATERIAL_MECHANICS_EXPORT_DIR;
    if (automatedExportDir) {
        const exportRoot = path.resolve(automatedExportDir);
        fs.mkdirSync(exportRoot, { recursive: true });
        filePath = path.join(exportRoot, requestedName);
        if (path.dirname(filePath) !== exportRoot) {
            throw new Error("导出路径无效。")
        }
    } else {
        const result = await dialog.showSaveDialog(mainWindow, {
            title: "导出实验报告",
            defaultPath: requestedName,
            filters: extension === ".md"
                ? [{ name: "Markdown", extensions: ["md"] }]
                : [{ name: "HTML", extensions: ["html"] }],
        });
        if (result.canceled || !result.filePath) return { saved: false };
        filePath = result.filePath;
    }

    fs.writeFileSync(filePath, content, "utf8");
    return { saved: true, filePath };
});

ipcMain.on("settings:close", () => {
    if (settingsWindow) settingsWindow.close();
});

if (!app.requestSingleInstanceLock()) {
    app.quit();
} else {
    app.on("second-instance", () => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });
    app.whenReady().then(async () => {
        createMenu();
        await createMainWindow();
    });
}

app.on("before-quit", () => {
    quitting = true;
    stopServer();
});

app.on("window-all-closed", () => {
    app.quit();
});
