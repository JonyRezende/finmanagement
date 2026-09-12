import { displayMonth } from "./state.js";
import { renderExtrato } from "./extrato.js";
import { renderProjection } from "./projection.js";
import { loadData } from "./api.js";
import {
  wireTxnForm,
  resetTransactionForm,
  showTransactionForm,
  hideTransactionForm,
} from "./txnForm.js";
import { wireCalculator } from "./calculator.js";

wireTxnForm();
wireCalculator();

document.getElementById("prevMonthBtn").addEventListener("click", () => {
  displayMonth.monthIndex--;
  if (displayMonth.monthIndex < 0) {
    displayMonth.monthIndex = 11;
    displayMonth.year--;
  }
  renderExtrato();
});

document.getElementById("nextMonthBtn").addEventListener("click", () => {
  displayMonth.monthIndex++;
  if (displayMonth.monthIndex > 11) {
    displayMonth.monthIndex = 0;
    displayMonth.year++;
  }
  renderExtrato();
});

document.getElementById("toggleFormBtn").addEventListener("click", () => {
  const form = document.getElementById("transactionForm");
  if (form.classList.contains("hidden")) {
    resetTransactionForm();
    showTransactionForm();
  } else {
    hideTransactionForm();
  }
});

document.addEventListener("click", (e) => {
  const form = document.getElementById("transactionForm");
  if (form.classList.contains("hidden")) return;
  const toggleBtn = document.getElementById("toggleFormBtn");
  if (
    form.contains(e.target) ||
    toggleBtn.contains(e.target) ||
    e.target.closest("[data-edit-id]") ||
    e.target.closest("#editScopeModal")
  )
    return;
  resetTransactionForm();
  hideTransactionForm();
});

document.getElementById("toggleProjectionBtn").addEventListener("click", () => {
  const root = document.getElementById("vizRoot");
  const hidden = root.classList.toggle("hidden");
  document.getElementById("toggleProjectionBtn").textContent = hidden ? "Mostrar projeção" : "Ocultar projeção";
  if (!hidden) renderProjection();
});

document.getElementById("toggleChartsBtn").addEventListener("click", () => {
  const container = document.getElementById("chartsContainer");
  const hidden = container.classList.toggle("hidden");
  document.getElementById("toggleChartsBtn").textContent = hidden ? "Mostrar gráficos" : "Ocultar gráficos";
  if (!hidden) renderProjection();
});

window.addEventListener("resize", () => {
  if (document.getElementById("vizRoot").classList.contains("hidden")) return;
  if (!document.getElementById("chartsContainer").classList.contains("hidden")) renderProjection();
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login.html";
});

loadData();