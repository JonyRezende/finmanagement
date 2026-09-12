import { test } from "node:test";
import assert from "node:assert/strict";
import { fmtMoney, formatAmountForInput, parseAmountInput, uid } from "../../public/js/money.js";

test("parseAmountInput strips formatting", () => {
  assert.equal(parseAmountInput("1.234,56"), 1234.56);
  assert.equal(parseAmountInput("0"), 0);
  assert.equal(parseAmountInput(""), 0);
});

test("formatAmountForInput renders pt-BR decimals", () => {
  assert.equal(formatAmountForInput(1234.56), "1.234,56");
  assert.equal(formatAmountForInput(0), "0,00");
});

test("parse/format roundtrip is stable", () => {
  for (const value of [1, 10.5, 1234.56, 999999.99]) {
    assert.equal(parseAmountInput(formatAmountForInput(value)), value);
  }
});

test("fmtMoney produces BRL", () => {
  assert.ok(fmtMoney(1234.56).includes("R$"));
  assert.ok(fmtMoney(1234.56).includes("1.234"));
});

test("uid is unique", () => {
  const a = uid();
  const b = uid();
  assert.notEqual(a, b);
  assert.ok(a.length > 0);
});