import { test } from "node:test";
import assert from "node:assert/strict";
import {
  effectiveStartMonth,
  isRecurrenceActiveInMonth,
  getMonthTransactions,
  computeProjection,
  balanceAtMonthStart,
} from "../../public/js/projections.js";

const REF = { year: 2026, monthIndex: 0 };

function rec(overrides = {}) {
  return {
    id: "r1",
    description: "Salário",
    type: "income",
    amount: "100",
    day: "5",
    startMonth: "2026-01",
    endMonth: null,
    overrides: {},
    hasInstallments: false,
    ...overrides,
  };
}

test("isRecurrenceActiveInMonth respects startMonth", () => {
  const r = rec();
  assert.equal(isRecurrenceActiveInMonth(r, 2025, 11, REF.year, REF.monthIndex), false);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 0, REF.year, REF.monthIndex), true);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 4, REF.year, REF.monthIndex), true);
});

test("isRecurrenceActiveInMonth respects endMonth", () => {
  const r = rec({ endMonth: "2026-03" });
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 3, REF.year, REF.monthIndex), false);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 2, REF.year, REF.monthIndex), true);
});

test("isRecurrenceActiveInMonth endDate keeps months up to the one in progress", () => {
  const r = rec({ endDate: "2026-03-15" });
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 1, REF.year, REF.monthIndex), true);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 2, REF.year, REF.monthIndex), false);
});

test("isRecurrenceActiveInMonth installments window", () => {
  const r = rec({ hasInstallments: true, installmentTotal: "3", installmentCurrent: "2" });
  assert.equal(isRecurrenceActiveInMonth(r, 2025, 11, REF.year, REF.monthIndex), false);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 0, REF.year, REF.monthIndex), true);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 1, REF.year, REF.monthIndex), true);
  assert.equal(isRecurrenceActiveInMonth(r, 2026, 2, REF.year, REF.monthIndex), false);
});

test("effectiveStartMonth falls back to date", () => {
  assert.equal(effectiveStartMonth(rec({ startMonth: null, date: "2025-12-10" })), "2025-12");
});

test("getMonthTransactions applies overrides and installment labels", () => {
  const r = rec({ overrides: { "2026-02": { amount: "999", description: "Salário ajustado" } } });
  const tx = getMonthTransactions([r], [], 2026, 1, REF.year, REF.monthIndex);
  assert.equal(tx.length, 1);
  assert.equal(tx[0].amount, 999);
  assert.equal(tx[0].description, "Salário ajustado");
});

test("getMonthTransactions mixes one-offs sorted by day", () => {
  const r = rec({ day: "10" });
  const items = [
    { id: "o1", description: "Bônus", type: "income", amount: "500", date: "2026-01-01" },
  ];
  const tx = getMonthTransactions([r], items, 2026, 0, REF.year, REF.monthIndex);
  assert.equal(tx.length, 2);
  assert.equal(tx[0].id, "o1");
  assert.equal(tx[1].id, "r1");
});

test("computeProjection totals and running balance", () => {
  const months = computeProjection(
    [rec()],
    [{ id: "o1", description: "Bônus", type: "income", amount: "500", date: "2026-01-10" }],
    REF.year,
    REF.monthIndex,
    3
  );
  assert.equal(months.length, 3);
  assert.equal(months[0].label, "Jan/26");
  assert.equal(months[0].income, 600);
  assert.equal(months[0].expense, 0);
  assert.equal(months[0].net, 600);
  assert.equal(months[0].endBalance, 600);
  assert.equal(months[1].income, 100);
  assert.equal(months[1].endBalance, 700);
  assert.equal(months[2].endBalance, 800);
});

test("computeProjection ignores month overrides (documented current behavior)", () => {
  const r = rec({ overrides: { "2026-02": { amount: "999" } } });
  const months = computeProjection([r], [], REF.year, REF.monthIndex, 3);
  assert.equal(months[1].income, 100);
});

test("balanceAtMonthStart carries negative offsets", () => {
  const r = rec({ startMonth: "2025-12" });
  const balance = balanceAtMonthStart([r], [], 0, REF.year, REF.monthIndex);
  assert.equal(balance, 100);
});