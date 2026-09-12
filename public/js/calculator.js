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

export function applyCalculator(calc, action, value) {
  if (action === "clear") {
    Object.assign(calc, { display: "0", expression: "", operand: null, operator: null, waitingForNext: false });
  } else if (action === "backspace") {
    if (!calc.waitingForNext && calc.display !== "Erro") {
      calc.display = calc.display.length > 1 ? calc.display.slice(0, -1) : "0";
      if (calc.operator) calc.expression = `${calc.operand} ${calculatorOperatorLabel(calc.operator)} ${calc.display}`;
    }
  } else if (action === "digit") {
    if (calc.waitingForNext || calc.display === "Erro") {
      calc.display = value;
      calc.waitingForNext = false;
      if (!calc.operator) calc.expression = "";
    } else {
      calc.display = calc.display === "0" ? value : calc.display + value;
    }
    if (calc.operator) calc.expression = `${calc.operand} ${calculatorOperatorLabel(calc.operator)} ${calc.display}`;
  } else if (action === "decimal") {
    if (calc.waitingForNext || calc.display === "Erro") {
      calc.display = "0,";
      calc.waitingForNext = false;
      if (!calc.operator) calc.expression = "";
    } else if (!calc.display.includes(",")) {
      calc.display += ",";
    }
    if (calc.operator) calc.expression = `${calc.operand} ${calculatorOperatorLabel(calc.operator)} ${calc.display}`;
  } else if (action === "operator") {
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
  } else if (action === "equals" && calc.operator && !calc.waitingForNext) {
    const expression = calc.expression;
    const result = calculatorResult(calc.operand, calculatorNumber(calc), calc.operator);
    setCalculatorResult(calc, result);
    calc.expression = `${expression} =`;
    calc.operand = null;
    calc.operator = null;
    calc.waitingForNext = true;
  }
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