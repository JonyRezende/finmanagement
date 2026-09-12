import { test } from "node:test";
import assert from "node:assert/strict";
import {
  MONTH_LABELS,
  MONTH_LABELS_FULL,
  daysInMonth,
  monthKeyFor,
  monthBefore,
  monthOffset,
  yearMonthAdd,
} from "../../public/js/calendar.js";

test("month labels have pt-BR entries", () => {
  assert.equal(MONTH_LABELS.length, 12);
  assert.equal(MONTH_LABELS[0], "Jan");
  assert.equal(MONTH_LABELS_FULL[0], "Janeiro");
});

test("daysInMonth handles leap year", () => {
  assert.equal(daysInMonth(2026, 1), 28);
  assert.equal(daysInMonth(2024, 1), 29);
});

test("monthKeyFor zero-pads", () => {
  assert.equal(monthKeyFor(2026, 0), "2026-01");
  assert.equal(monthKeyFor(2026, 11), "2026-12");
});

test("monthBefore wraps year", () => {
  assert.equal(monthBefore("2026-01"), "2025-12");
  assert.equal(monthBefore("2026-07"), "2026-06");
});

test("monthOffset counts months from reference", () => {
  assert.equal(monthOffset(2026, 0, 2026, 0), 0);
  assert.equal(monthOffset(2026, 0, 2027, 11), 23);
  assert.equal(monthOffset(2026, 0, 2025, 0), -12);
});

test("yearMonthAdd wraps around year boundary", () => {
  assert.deepEqual(yearMonthAdd(2026, 0, -1), { year: 2025, monthIndex: 11 });
  assert.deepEqual(yearMonthAdd(2026, 0, 13), { year: 2027, monthIndex: 1 });
});