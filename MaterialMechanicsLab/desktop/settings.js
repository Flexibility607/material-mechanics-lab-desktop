"use strict";

const status = document.getElementById("status");
const apiKey = document.getElementById("apiKey");
const model = document.getElementById("model");
const clearKey = document.getElementById("clearKey");
const saveButton = document.getElementById("save");
const message = document.getElementById("message");

window.settingsAPI.get().then((settings) => {
    status.textContent = settings.configured ? "当前已配置 API 密钥" : "当前未配置 API 密钥";
    status.dataset.kind = settings.configured ? "ok" : "bad";
    model.value = settings.model || "gpt-5-mini";
}).catch((error) => {
    status.textContent = "读取失败：" + error.message;
    status.dataset.kind = "bad";
});

clearKey.addEventListener("change", () => {
    apiKey.disabled = clearKey.checked;
});

document.getElementById("cancel").addEventListener("click", () => window.settingsAPI.close());

saveButton.addEventListener("click", async () => {
    saveButton.disabled = true;
    message.textContent = "正在保存并重启本地服务…";
    try {
        await window.settingsAPI.save({
            apiKey: apiKey.value,
            model: model.value.trim(),
            clearKey: clearKey.checked
        });
        message.textContent = "保存成功。";
        window.setTimeout(() => window.settingsAPI.close(), 500);
    } catch (error) {
        message.textContent = "保存失败：" + error.message;
        saveButton.disabled = false;
    }
});
