const form = document.querySelector("#form");
const input = document.querySelector("#repo");
const button = document.querySelector("#generate");
const error = document.querySelector("#error");
const status = document.querySelector("#status");
const result = document.querySelector("#result");
const loading = document.querySelector("#loading");
const image = document.querySelector("#thumbnail");
const actions = document.querySelector("#actions");
const download = document.querySelector("#download");

let busy = false;
let imageUrl = null; // the shown thumbnail, kept in the browser's memory until it's replaced

form.addEventListener("submit", (event) => {
  event.preventDefault(); // handle it here instead of leaving the page
  generate(input.value.trim());
});

// A shared address like /?repo=pallets/flask fills in the box and makes that thumbnail.
const shared = new URLSearchParams(location.search).get("repo");
if (shared) {
  input.value = shared;
  generate(shared.trim());
}

async function generate(link) {
  if (busy) return; // one request at a time, so double-clicks don't use up GitHub calls
  if (!link) {
    showError("Enter a GitHub repository link, like github.com/owner/repo.");
    return;
  }

  setBusy(true);
  try {
    // The server redirects this to the repo's own address, and fetch follows it.
    const response = await fetch(`/api/thumbnail?repo=${encodeURIComponent(link)}`);
    if (response.ok) {
      showThumbnail(await response.blob(), response);
    } else {
      showError(await errorMessage(response));
    }
  } catch {
    showError("Couldn't reach the server. Check your connection and try again.");
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  busy = isBusy;
  button.disabled = isBusy;
  button.textContent = isBusy ? "Generating…" : "Generate Thumbnail";
  loading.hidden = !isBusy;
  if (isBusy) {
    error.hidden = true;
    result.hidden = false;
    image.hidden = true;
    actions.hidden = true;
    status.textContent = "Generating thumbnail…";
  }
}

function showThumbnail(blob, response) {
  // response.url is where the redirect led: /api/thumbnail/<owner>/<repo>.png
  const [owner, file] = new URL(response.url).pathname.split("/").slice(-2);
  const repo = file.replace(/\.png$/, "");
  const disposition = response.headers.get("Content-Disposition") || "";
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? `${owner}_${repo}.png`;

  if (imageUrl) URL.revokeObjectURL(imageUrl);
  imageUrl = URL.createObjectURL(blob);
  image.src = imageUrl;
  image.alt = `Thumbnail for ${owner}/${repo}`;
  image.hidden = false;
  download.href = imageUrl;
  download.download = filename;
  actions.hidden = false;
  status.textContent = "Thumbnail ready.";

  // Put the repo in the address bar, so copying it shares this thumbnail.
  history.replaceState(null, "", `?repo=${owner}/${repo}`);
}

function showError(message) {
  error.textContent = message;
  error.hidden = false;
  result.hidden = true;
  status.textContent = "";
  history.replaceState(null, "", location.pathname); // don't keep sharing the last thumbnail
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    if (body.error) return body.error;
  } catch {
    // Not our JSON, e.g. a timeout page from the host.
  }
  if (response.status === 429) {
    // The host's firewall, not our app: this visitor has asked for a lot of thumbnails at once.
    return "You've made a lot of thumbnails in a short time. Please wait a few minutes and try again.";
  }
  return `Something went wrong (error ${response.status}). Please try again.`;
}
