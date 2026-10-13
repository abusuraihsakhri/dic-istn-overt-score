"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { calculateOvertDIC } = require("./scoring.js");

const make = (overrides = {}) => ({
  underlyingCondition: true, platelets: 150, fibrinMarker: "no_increase",
  ptProlongation: 0, fibrinogen: 2, ...overrides
});

test("all normal yields zero", () => {
  assert.equal(calculateOvertDIC(make()).total, 0);
});

test("score exactly 5 is compatible", () => {
  const r = calculateOvertDIC(make({
    platelets: 80, fibrinMarker: "moderate_increase",
    ptProlongation: 4, fibrinogen: 0.9
  }));
  assert.equal(r.total, 5);
  assert.equal(r.compatible, true);
});

test("exact boundary values follow ISTH definitions", () => {
  const r = calculateOvertDIC(make({
    platelets: 100, ptProlongation: 6, fibrinogen: 1
  }));
  assert.deepEqual(r.components, {
    platelets: 0, fibrinMarker: 0, pt: 2, fibrinogen: 0
  });
});

test("maximum eight points", () => {
  assert.equal(calculateOvertDIC(make({
    platelets: 10, fibrinMarker: "strong_increase",
    ptProlongation: 7, fibrinogen: 0.5
  })).total, 8);
});

test("invalid or missing values are not silently scored", () => {
  for (const value of ["", "-1", "Infinity", "NaN", "abc", null]) {
    assert.throws(() => calculateOvertDIC(make({ platelets: value })));
  }
  assert.throws(() => calculateOvertDIC(make({ fibrinMarker: "5.0" })));
  assert.throws(() => calculateOvertDIC(make({ underlyingCondition: false })));
});
