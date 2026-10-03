// SENIM: send the selected AI answer to the SENIM site for a fact check.
// The text travels in the URL hash (/check#text=…), which the browser never sends to any server.

const DEFAULT_SITE = "https://senim-fawn.vercel.app";
const MAX_CHARS = 8000;

async function siteUrl() {
  const { site } = await chrome.storage.sync.get({ site: DEFAULT_SITE });
  return (site || DEFAULT_SITE).replace(/\/+$/, "");
}

async function openCheck(text, tab) {
  const clean = (text || "").trim().slice(0, MAX_CHARS);
  const url = `${await siteUrl()}/check` + (clean ? `#text=${encodeURIComponent(clean)}` : "");
  chrome.tabs.create({ url, index: tab ? tab.index + 1 : undefined });
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "senim-check", title: chrome.i18n.getMessage("menu"), contexts: ["selection"] });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "senim-check") openCheck(info.selectionText, tab);
});

// Toolbar button / Alt+Shift+S: check whatever is selected on the page (or open an empty check).
chrome.action.onClicked.addListener(async (tab) => {
  let text = "";
  try {
    const [res] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => String(window.getSelection() || ""),
    });
    text = res?.result || "";
  } catch {
    // chrome:// pages and the Web Store cannot be scripted: just open the checker.
  }
  openCheck(text, tab);
});
