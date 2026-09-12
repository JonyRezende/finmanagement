import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createCalculator,
  applyCalculator,
  calculatorResult,
  calculatorOperatorLabel,
} from "../../public/js/calculator.js";

test("digit entry replaces leading zero", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "0");
  applyCalculator(calc, "digit", "5");
  assert.equal(calc.display, "5");
});

test("addition chain", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "5");
  applyCalculator(calc, "operator", "+");
  applyCalculator(calc, "digit", "3");
  applyCalculator(calc, "equals");
  assert.equal(calc.display, "8");
  assert.equal(calc.expression, "5 + 3 =");
});

test("division by zero shows Erro", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "7");
  applyCalculator(calc, "operator", "/");
  applyCalculator(calc, "digit", "0");
  applyCalculator(calc, "equals");
  assert.equal(calc.display, "Erro");
});

test("chained operators reduce immediately", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "6");
  applyCalculator(calc, "operator", "*");
  applyCalculator(calc, "digit", "7");
  applyCalculator(calc, "operator", "+");
  assert.equal(calc.display, "42");
  applyCalculator(calc, "digit", "8");
  applyCalculator(calc, "equals");
  assert.equal(calc.display, "50");
});

test("backspace", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "1");
  applyCalculator(calc, "digit", "2");
  applyCalculator(calc, "backspace");
  assert.equal(calc.display, "1");
  applyCalculator(calc, "backspace");
  assert.equal(calc.display, "0");
});

test("decimal entry", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "1");
  applyCalculator(calc, "decimal");
  applyCalculator(calc, "digit", "5");
  assert.equal(calc.display, "1,5");
});

test("clear resets all state", () => {
  const calc = createCalculator();
  applyCalculator(calc, "digit", "9");
  applyCalculator(calc, "operator", "*");
  applyCalculator(calc, "clear");
  assert.deepEqual(calc, createCalculator());
});

test("calculatorResult helpers", () => {
  assert.equal(calculatorResult(10, 3, "+"), 13);
  assert.equal(calculatorResult(10, 3, "-"), 7);
  assert.equal(calculatorResult(10, 3, "*"), 30);
  assert.equal(calculatorResult(10, 3, "/"), 10 / 3);
  assert.equal(calculatorResult(10, 0, "/"), null);
  assert.equal(calculatorOperatorLabel("/"), "÷");
  assert.equal(calculatorOperatorLabel("+"), "+");
});