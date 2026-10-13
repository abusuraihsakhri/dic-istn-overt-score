/* Classic ISTH overt-DIC point score. Browser and Node.js compatible. */
(function (root) {
  "use strict";
  const pointsForMarker = Object.freeze({
    no_increase: 0, moderate_increase: 2, strong_increase: 3
  });

  function finiteNonnegative(value, label) {
    if (value === "" || value === null || value === undefined ||
        typeof value === "boolean") {
      throw new Error(label + " is required.");
    }
    const n = Number(value);
    if (!Number.isFinite(n) || n < 0) {
      throw new Error(label + " must be a finite, non-negative number.");
    }
    return n;
  }

  function calculateOvertDIC(values) {
    if (!values || values.underlyingCondition !== true) {
      throw new Error("Confirm an underlying condition associated with DIC before applying this scoring system.");
    }
    const platelets = finiteNonnegative(values.platelets, "Platelet count");
    const pt = finiteNonnegative(values.ptProlongation, "PT prolongation");
    const fibrinogen = finiteNonnegative(values.fibrinogen, "Fibrinogen");
    if (!Object.prototype.hasOwnProperty.call(pointsForMarker, values.fibrinMarker)) {
      throw new Error("Select an assay-interpreted fibrin marker category.");
    }
    const components = {
      platelets: platelets < 50 ? 2 : platelets < 100 ? 1 : 0,
      fibrinMarker: pointsForMarker[values.fibrinMarker],
      pt: pt >= 6 ? 2 : pt >= 3 ? 1 : 0,
      fibrinogen: fibrinogen < 1 ? 1 : 0
    };
    const total = Object.values(components).reduce((a, b) => a + b, 0);
    return {
      components,
      total,
      compatible: total >= 5,
      interpretation: total >= 5
        ? "Compatible with overt DIC in an appropriate clinical context."
        : "Below the overt-DIC threshold; does not exclude early or evolving DIC."
    };
  }

  const api = Object.freeze({ calculateOvertDIC });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.DICScoring = api;
})(typeof window !== "undefined" ? window : undefined);
