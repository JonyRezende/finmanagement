export function calculatorOperatorLabel(operator) {
  return { "/": "÷", "*": "×" }[operator] || operator;
}

export function createCalculator() {
  return { display: "0", expression: "", operand: null, operator: null, waitingForNext: false };
}

export function calculatorNumber(calc) {
  return Number(calc.display.replace(",", "."));
}

export function calculatorResult(left, right, operator) {
  if (operator === "+") return left + right;
  if (operator === "-") return left - right;
  if (operator === "*") return left * right;
  if (operator === "/") return right === 0 ? null : left / right;
  return right;
}

export function setCalculatorResult(calc, result) {
  calc.display =
    result === null || !Number.isFinite(result)
      ? "Erro"
      : String(Number(result.toFixed(10))).replace(".", ",");
}

function updateExpression(calc) {
  if (calc.operator) calc.expression = `${calc.operand} ${calculatorOperatorLabel(calc.operator)} ${calc.display}`;
}

function startFreshInput(calc, value) {
  calc.display = value;
  calc.waitingForNext = false;
  if (!calc.operator) calc.expression = "";
}

function doClear(calc) {
  Object.assign(calc, { display: "0", expression: "", operand: null, operator: null, waitingForNext: false });
}

function doBackspace(calc) {
  if (calc.waitingForNext || calc.display === "Erro") return;
  calc.display = calc.display.length > 1 ? calc.display.slice(0, -1) : "0";
  updateExpression(calc);
}

function doDigit(calc, value) {
  if (calc.waitingForNext || calc.display === "Erro") startFreshInput(calc, value);
  else calc.display = calc.display === "0" ? value : calc.display + value;
  updateExpression(calc);
}

function doDecimal(calc) {
  if (calc.waitingForNext || calc.display === "Erro") startFreshInput(calc, "0,");
  else if (!calc.display.includes(",")) calc.display += ",";
  updateExpression(calc);
}

function doOperator(calc, value) {
  const current = calculatorNumber(calc);
  if (calc.operator && !calc.waitingForNext) {
    const result = calculatorResult(calc.operand, current, calc.operator);
    setCalculatorResult(calc, result);
    calc.operand = result;
  } else {
    calc.operand = current;
  }
  calc.operator = value;
  calc.waitingForNext = true;
  calc.expression = `${calc.display} ${calculatorOperatorLabel(value)}`;
}

function doEquals(calc) {
  if (!calc.operator || calc.waitingForNext) return;
  const expression = calc.expression;
  const result = calculatorResult(calc.operand, calculatorNumber(calc), calc.operator);
  setCalculatorResult(calc, result);
  calc.expression = `${expression} =`;
  calc.operand = null;
  calc.operator = null;
  calc.waitingForNext = true;
}

const CALC_ACTIONS = {
  clear: doClear,
  backspace: doBackspace,
  digit: doDigit,
  decimal: doDecimal,
  operator: doOperator,
  equals: doEquals,
};

export function applyCalculator(calc, action, value) {
  if (!CALC_ACTIONS[action]) return;
  CALC_ACTIONS[action](calc, value);
}

export function wireCalculator() {
  const calculator = createCalculator();
  function renderCalculator() {
    document.getElementById("calculatorDisplay").textContent = calculator.display;
    document.getElementById("calculatorExpression").textContent = calculator.expression;
    document.querySelectorAll('[data-calc="operator"]').forEach((button) => {
      button.classList.toggle("is-active", button.dataset.value === calculator.operator);
    });
  }
  document.querySelectorAll("[data-calc]").forEach((button) => {
    button.addEventListener("click", () => {
      applyCalculator(calculator, button.dataset.calc, button.dataset.value);
      renderCalculator();
    });
  });
}