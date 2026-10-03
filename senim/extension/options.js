for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = chrome.i18n.getMessage(el.dataset.i18n);

const input = document.getElementById("site");
chrome.storage.sync.get({ site: "https://senim-fawn.vercel.app" }, ({ site }) => (input.value = site));

document.getElementById("save").addEventListener("click", () => {
  let site = input.value.trim();
  try {
    const u = new URL(site);
    if (u.protocol !== "https:" && u.hostname !== "localhost") throw new Error();
    site = u.origin;
  } catch {
    input.focus();
    return;
  }
  chrome.storage.sync.set({ site }, () => (document.getElementById("saved").textContent = " ✓"));
});
