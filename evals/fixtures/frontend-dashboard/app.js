const queryInput = document.querySelector("#query");
const searchButton = document.querySelector("#search-button");
const status = document.querySelector("#status");
const results = document.querySelector("#results");

const fixtures = {
  acme: ["ACME — Checkout timeout", "ACME — Duplicate confirmation email"],
  beta: ["Beta Labs — Account recovery loop"],
};

function fetchIncidents(query) {
  const normalized = query.trim().toLowerCase();
  const delay = normalized === "acme" ? 450 : 60;
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(fixtures[normalized] || []), delay);
  });
}

async function runSearch() {
  const submittedQuery = queryInput.value;
  status.textContent = `Searching for ${submittedQuery}…`;
  results.classList.add("is-updating");

  const incidents = await fetchIncidents(submittedQuery);
  results.replaceChildren(
    ...incidents.map((incident) => {
      const item = document.createElement("li");
      item.className = "result";
      item.textContent = incident;
      return item;
    }),
  );
  results.classList.remove("is-updating");
  status.textContent = `${incidents.length} results for ${submittedQuery}`;
}

searchButton.addEventListener("click", runSearch);
window.runPulseboardSearch = runSearch;
