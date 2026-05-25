const EMPTY_OPERATORS = new Set(["is_empty", "is_not_empty"]);
const EMPTY_OPERATOR_OPTIONS = [
  { value: "is_empty", label: "is empty" },
  { value: "is_not_empty", label: "is not empty" },
];

const TABLE_COLUMNS = [
  { key: "number", label: "Number" },
  { key: "short_description", label: "Short Description" },
  { key: "state", label: "State" },
  { key: "priority", label: "Priority" },
  { key: "active", label: "Active" },
  { key: "assignment_group", label: "Assignment Group" },
  { key: "caller", label: "Caller" },
  { key: "assigned_to", label: "Assigned To" },
  { key: "sys_created_on", label: "Created" },
];

const STATE_OPTIONS = [
  { value: "1", label: "New" },
  { value: "2", label: "In Progress" },
  { value: "3", label: "On Hold" },
  { value: "6", label: "Resolved" },
  { value: "7", label: "Closed" },
  { value: "8", label: "Canceled" },
];

const ACTIVE_OPTIONS = [
  { value: "true", label: "Active" },
  { value: "false", label: "Inactive" },
];

function withEmptyOperators(operators) {
  return [...operators, ...EMPTY_OPERATOR_OPTIONS];
}

function textField(label, placeholder) {
  return {
    label,
    operators: withEmptyOperators([
      { value: "contains", label: "contains" },
      { value: "is", label: "is" },
    ]),
    input: "text",
    placeholder,
  };
}

const FIELD_CONFIG = {
  number: {
    label: "Number",
    operators: withEmptyOperators([
      { value: "is", label: "is" },
      { value: "contains", label: "contains" },
    ]),
    input: "text",
    placeholder: "INC0010001",
  },
  short_description: textField("Short description", "network outage"),
  assignment_group: textField("Assignment group", "Network"),
  caller: textField("Caller", "John Smith"),
  assigned_to: textField("Assigned to", "Jane Doe"),
  state: {
    label: "State",
    operators: withEmptyOperators([{ value: "is", label: "is" }]),
    input: "select",
    options: STATE_OPTIONS,
  },
  active: {
    label: "Active",
    operators: withEmptyOperators([{ value: "is", label: "is" }]),
    input: "select",
    options: ACTIVE_OPTIONS,
  },
  created: {
    label: "Created date",
    operators: withEmptyOperators([
      { value: "on_or_after", label: "on or after" },
      { value: "on_or_before", label: "on or before" },
    ]),
    input: "date",
  },
};

const form = document.getElementById("search-form");
const groupsEl = document.getElementById("groups");
const addGroupButton = document.getElementById("add-group");
const resetButton = document.getElementById("reset-button");
const searchButton = document.getElementById("search-button");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

let rowCounter = 0;
let groupCounter = 0;
let lastIncidents = [];

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.className = isError ? "status error" : "status";
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isEmptyOperator(operator) {
  return EMPTY_OPERATORS.has(operator);
}

function getOperators(fieldName) {
  return FIELD_CONFIG[fieldName].operators;
}

function renderOperatorOptions(fieldName, selectedOperator) {
  return getOperators(fieldName)
    .map(
      (operator) => `
        <option value="${operator.value}" ${operator.value === selectedOperator ? "selected" : ""}>
          ${operator.label}
        </option>
      `
    )
    .join("");
}

function renderValueInput(fieldName, operator, value = "") {
  if (isEmptyOperator(operator)) {
    return `<input class="value-input" data-role="value" type="text" value="" placeholder="No value needed" disabled />`;
  }

  const config = FIELD_CONFIG[fieldName];

  if (config.input === "select") {
    const options = config.options
      .map(
        (option) => `
          <option value="${option.value}" ${option.value === value ? "selected" : ""}>
            ${option.label}
          </option>
        `
      )
      .join("");
    return `<select class="value-input" data-role="value">${options}</select>`;
  }

  if (config.input === "date") {
    return `<input class="value-input" data-role="value" type="date" value="${escapeHtml(value)}" />`;
  }

  return `<input class="value-input" data-role="value" type="text" value="${escapeHtml(value)}" placeholder="${config.placeholder || ""}" />`;
}

function renderJoinSelect(selectedJoin = "and") {
  return `
    <select data-role="join" class="join-select" aria-label="Join with previous condition">
      <option value="and" ${selectedJoin === "and" ? "selected" : ""}>AND</option>
      <option value="or" ${selectedJoin === "or" ? "selected" : ""}>OR</option>
    </select>
  `;
}

function updateValueCell(row, fieldName, operator) {
  row.querySelector('[data-role="value-cell"]').innerHTML = renderValueInput(fieldName, operator);
}

function createConditionRow(initial = {}) {
  rowCounter += 1;
  const fieldName = initial.field || "short_description";
  const operator = initial.operator || getOperators(fieldName)[0].value;
  const row = document.createElement("div");
  row.className = "condition-row";
  row.dataset.rowId = `condition-${rowCounter}`;
  row.dataset.join = initial.join || "and";

  row.innerHTML = `
    <div class="join-cell"></div>
    <select data-role="field">
      ${Object.entries(FIELD_CONFIG)
        .map(
          ([key, config]) => `
            <option value="${key}" ${key === fieldName ? "selected" : ""}>${config.label}</option>
          `
        )
        .join("")}
    </select>
    <select data-role="operator">
      ${renderOperatorOptions(fieldName, operator)}
    </select>
    <div data-role="value-cell">
      ${renderValueInput(fieldName, operator, initial.value || "")}
    </div>
    <button type="button" class="remove-btn" data-role="remove-condition" title="Remove condition">&times;</button>
  `;

  return row;
}

function refreshGroupControls(groupEl) {
  const rows = groupEl.querySelectorAll(".condition-row");
  rows.forEach((row, index) => {
    const joinCell = row.querySelector(".join-cell");
    if (index === 0) {
      joinCell.innerHTML = '<span class="join-where">Where</span>';
    } else {
      const currentJoin = row.querySelector('[data-role="join"]')?.value || row.dataset.join || "and";
      joinCell.innerHTML = renderJoinSelect(currentJoin);
    }
    row.querySelector('[data-role="remove-condition"]').disabled = rows.length === 1;
  });
}

function createConditionGroup(initialConditions = [{}]) {
  groupCounter += 1;
  const groupEl = document.createElement("section");
  groupEl.className = "condition-group";
  groupEl.dataset.groupId = `group-${groupCounter}`;
  groupEl.innerHTML = `
    <div class="group-header">
      <div class="group-title">Match set</div>
      <button type="button" class="group-remove" data-role="remove-group">Remove set</button>
    </div>
    <div class="group-body" data-role="group-body"></div>
    <div class="group-footer">
      <button type="button" class="btn-ghost" data-role="add-condition">+ Add condition</button>
    </div>
  `;

  const body = groupEl.querySelector('[data-role="group-body"]');
  initialConditions.forEach((condition) => body.appendChild(createConditionRow(condition)));
  refreshGroupControls(groupEl);
  return groupEl;
}

function refreshGroupTitles() {
  const groups = groupsEl.querySelectorAll(".condition-group");
  groups.forEach((groupEl, index) => {
    groupEl.querySelector(".group-title").textContent = `Match set ${index + 1}`;
    groupEl.querySelector('[data-role="remove-group"]').style.visibility =
      groups.length === 1 ? "hidden" : "visible";
  });
}

function renderGroupLayout() {
  const groups = Array.from(groupsEl.querySelectorAll(".condition-group"));
  groupsEl.innerHTML = "";
  groups.forEach((groupEl, index) => {
    if (index > 0) {
      const divider = document.createElement("div");
      divider.className = "group-divider";
      divider.innerHTML = "<span>OR</span>";
      groupsEl.appendChild(divider);
    }
    groupsEl.appendChild(groupEl);
  });
  refreshGroupTitles();
}

function addGroup(initialConditions = [{}]) {
  groupsEl.appendChild(createConditionGroup(initialConditions));
  renderGroupLayout();
}

function resetBuilder() {
  groupsEl.innerHTML = "";
  groupCounter = 0;
  lastIncidents = [];
  addGroup([{ field: "short_description", operator: "contains" }]);
  setStatus("");
  resultsEl.innerHTML = "";
}

function parseApiError(data, fallback) {
  const detail = data.detail || fallback;
  return typeof detail === "string" ? detail : JSON.stringify(detail);
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  return { response, data };
}

async function exportToExcel() {
  if (!lastIncidents.length) {
    setStatus("Run a search before exporting.", true);
    return;
  }

  try {
    const response = await fetch("/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ incidents: lastIncidents }),
    });

    if (!response.ok) {
      const data = await response.json();
      setStatus(parseApiError(data, "Export failed."), true);
      return;
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "");
    link.href = url;
    link.download = `incidents_${timestamp}.xlsx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    setStatus("Unable to export incidents.", true);
  }
}

function renderIncidents(incidents) {
  lastIncidents = incidents;

  if (!incidents.length) {
    resultsEl.innerHTML = '<div class="empty">No incidents matched your conditions.</div>';
    return;
  }

  const headerCells = TABLE_COLUMNS.map((column) => `<th>${column.label}</th>`).join("");
  const rows = incidents
    .map(
      (incident) => `
        <tr>
          ${TABLE_COLUMNS.map((column) => `<td>${escapeHtml(incident[column.key] ?? "")}</td>`).join("")}
        </tr>
      `
    )
    .join("");

  resultsEl.innerHTML = `
    <div class="results-header">
      <div class="results-count">${incidents.length} incident${incidents.length === 1 ? "" : "s"}</div>
      <button type="button" class="btn-primary" id="export-button">Export to Excel</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr>${headerCells}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;

  document.getElementById("export-button").addEventListener("click", exportToExcel);
}

function collectGroups() {
  const groups = [];

  groupsEl.querySelectorAll(".condition-group").forEach((groupEl) => {
    const conditions = [];

    groupEl.querySelectorAll(".condition-row").forEach((row, index) => {
      const field = row.querySelector('[data-role="field"]').value;
      const operator = row.querySelector('[data-role="operator"]').value;
      const value = row.querySelector('[data-role="value"]').value.trim();

      if (!isEmptyOperator(operator) && !value) {
        throw new Error(`Enter a value for "${FIELD_CONFIG[field].label}".`);
      }

      const condition = {
        field,
        operator,
        value: isEmptyOperator(operator) ? "" : value,
      };
      if (index > 0) {
        condition.join = row.querySelector('[data-role="join"]').value;
      }
      conditions.push(condition);
    });

    groups.push({ conditions });
  });

  return groups;
}

groupsEl.addEventListener("change", (event) => {
  const row = event.target.closest(".condition-row");
  if (!row) {
    return;
  }

  const role = event.target.dataset.role;
  if (role === "field") {
    const fieldName = event.target.value;
    const operatorSelect = row.querySelector('[data-role="operator"]');
    const defaultOperator = getOperators(fieldName)[0].value;
    operatorSelect.innerHTML = renderOperatorOptions(fieldName, defaultOperator);
    updateValueCell(row, fieldName, defaultOperator);
    return;
  }

  if (role === "operator") {
    updateValueCell(row, row.querySelector('[data-role="field"]').value, event.target.value);
  }
});

groupsEl.addEventListener("click", (event) => {
  const groupEl = event.target.closest(".condition-group");
  if (!groupEl) {
    return;
  }

  const role = event.target.dataset.role;

  if (role === "add-condition") {
    groupEl.querySelector('[data-role="group-body"]').appendChild(createConditionRow());
    refreshGroupControls(groupEl);
    return;
  }

  if (role === "remove-condition" && !event.target.disabled) {
    event.target.closest(".condition-row").remove();
    refreshGroupControls(groupEl);
    return;
  }

  if (role === "remove-group") {
    groupEl.remove();
    groupsEl.querySelectorAll(".group-divider").forEach((divider) => divider.remove());
    renderGroupLayout();
  }
});

addGroupButton.addEventListener("click", () => addGroup([{}]));
resetButton.addEventListener("click", resetBuilder);

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  let groups;
  try {
    groups = collectGroups();
  } catch (error) {
    setStatus(error.message, true);
    return;
  }

  searchButton.disabled = true;
  setStatus("Searching...");
  resultsEl.innerHTML = "";

  try {
    const { response, data } = await postJson("/search", { groups });

    if (!response.ok) {
      setStatus(parseApiError(data, "Search failed."), true);
      return;
    }

    setStatus(`Found ${data.count} incident${data.count === 1 ? "" : "s"}.`);
    renderIncidents(data.incidents);
  } catch (error) {
    setStatus("Unable to reach the search API.", true);
  } finally {
    searchButton.disabled = false;
  }
});

resetBuilder();
