"use strict";

const form = document.getElementById("dic-form");
const status = document.getElementById("status");
const result = document.getElementById("result");
const exportButton = document.getElementById("export");
let exportText = "";

function setStatus(message, isError) {
  status.textContent = message;
  status.classList.toggle("error", isError);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    underlyingCondition: document.getElementById("underlying").checked,
    platelets: document.getElementById("platelets").value,
    fibrinMarker: document.getElementById("marker").value,
    ptProlongation: document.getElementById("pt").value,
    fibrinogen: document.getElementById("fibrinogen").value
  };
  exportButton.disabled = true;
  exportText = "";
  try {
    const assessment = window.DICScoring.calculateOvertDIC(payload);
    document.getElementById("score").textContent = assessment.total + " / 8";
    document.getElementById("interpretation").textContent = assessment.interpretation;
    for (const [key, value] of Object.entries(assessment.components)) {
      document.getElementById("point-" + key).textContent = value + " point" + (value === 1 ? "" : "s");
    }
    result.hidden = false;
    result.classList.toggle("positive", assessment.compatible);
    exportText = [
      "ISTH Overt DIC score (classic categorical algorithm)",
      "Platelets (x10^9/L): " + payload.platelets,
      "Fibrin marker: " + payload.fibrinMarker,
      "PT prolongation (s): " + payload.ptProlongation,
      "Fibrinogen (g/L): " + payload.fibrinogen,
      "Total: " + assessment.total + " / 8",
      "Interpretation: " + assessment.interpretation,
      "Scores require an underlying DIC-associated condition and clinical assessment.",
      "For educational and research use. Not a diagnostic or treatment recommendation."
    ].join("\n") + "\n";
    exportButton.disabled = false;
    setStatus("Calculated locally in your browser; no data sent to a server.", false);
  } catch (error) {
    result.hidden = true;
    setStatus(error.message, true);
  }
});

exportButton.addEventListener("click", () => {
  if (!exportText) return;
  const url = URL.createObjectURL(new Blob([exportText], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "isth-overt-dic-score.txt";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
});
