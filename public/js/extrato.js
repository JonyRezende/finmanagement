import { state, displayMonth, referenceMonth } from "./state.js";
import { MONTH_LABELS_FULL, monthOffset } from "./calendar.js";
import { fmtMoney } from "./money.js";
import { escapeHtml } from "./dom.js";
import { getMonthTransactions, balanceAtMonthStart } from "./projections.js";
import { handleEditClick, deleteTransaction } from "./txnForm.js";

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function renderExtrato() {
  document.getElementById("monthLabel").textContent = `${MONTH_LABELS_FULL[displayMonth.monthIndex]}/${displayMonth.year}`;

  const ref = referenceMonth();
  const offset = monthOffset(ref.year, ref.monthIndex, displayMonth.year, displayMonth.monthIndex);
  const startBalance = balanceAtMonthStart(state.recurrences, state.oneOffs, offset, ref.year, ref.monthIndex);
  const transactions = getMonthTransactions(state.recurrences, state.oneOffs, displayMonth.year, displayMonth.monthIndex, ref.year, ref.monthIndex);

  const body = document.getElementById("extratoBody");
  body.innerHTML = "";

  const startRow = document.createElement("tr");
  startRow.className = "extrato-summary-row";
  startRow.innerHTML = `<td>Saldo do mês anterior</td><td class="extrato-value"><strong>${fmtMoney(startBalance)}</strong></td><td></td>`;
  body.appendChild(startRow);

  if (transactions.length === 0) {
    const emptyRow = document.createElement("tr");
    emptyRow.innerHTML = `<td colspan="3" class="extrato-empty">Nenhuma transação prevista neste mês.</td>`;
    body.appendChild(emptyRow);
    return;
  }

  const groups = [];
  for (const t of transactions) {
    const key = t.date.toDateString();
    let group = groups.find((g) => g.key === key);
    if (!group) {
      group = { key, date: t.date, items: [] };
      groups.push(group);
    }
    group.items.push(t);
  }

  let running = startBalance;
  for (const group of groups) {
    const weekday = capitalize(group.date.toLocaleDateString("pt-BR", { weekday: "long" }));
    const dateLabel = group.date.toLocaleDateString("pt-BR");

    const dateRow = document.createElement("tr");
    dateRow.className = "extrato-date-row day-frame-top";
    dateRow.innerHTML = `<td colspan="3"><span class="extrato-date-badge">${dateLabel}, ${weekday}</span></td>`;
    body.appendChild(dateRow);

    for (const t of group.items) {
      running += t.type === "income" ? t.amount : -t.amount;
      const sign = t.type === "income" ? "+" : "-";
      const valueClass = t.type === "income" ? "amount-income" : "amount-expense";
      const tag =
        t.kind === "recurrence"
          ? `<span class="extrato-tag">${t.installmentLabel ? `parcela ${t.installmentLabel}` : "recorrente"}</span>`
          : "";
      const row = document.createElement("tr");
      row.className = "day-frame-item";
      row.innerHTML = `
        <td>${escapeHtml(t.description)}${tag}</td>
        <td class="extrato-value ${valueClass}">${sign} ${fmtMoney(t.amount)}</td>
        <td class="extrato-actions">
          <button class="btn-icon-sm btn-icon-edit" data-edit-kind="${t.kind}" data-edit-id="${t.id}" title="Editar" aria-label="Editar">✎</button>
          <button class="btn-icon-sm btn-icon-delete" data-delete-kind="${t.kind}" data-delete-id="${t.id}" title="Excluir" aria-label="Excluir">✕</button>
        </td>`;
      body.appendChild(row);
    }

    const totalRow = document.createElement("tr");
    totalRow.className = "extrato-summary-row day-frame-bottom";
    totalRow.innerHTML = `<td colspan="2" class="extrato-value"><span class="extrato-summary-label">Saldo do dia</span><strong>${fmtMoney(running)}</strong></td><td></td>`;
    body.appendChild(totalRow);

    const gapRow = document.createElement("tr");
    gapRow.className = "day-frame-gap";
    gapRow.innerHTML = `<td colspan="3"></td>`;
    body.appendChild(gapRow);
  }

  body.querySelectorAll("[data-edit-id]").forEach((btn) =>
    btn.addEventListener("click", () => handleEditClick(btn.dataset.editKind, btn.dataset.editId))
  );
  body.querySelectorAll("[data-delete-id]").forEach((btn) =>
    btn.addEventListener("click", () => deleteTransaction(btn.dataset.deleteKind, btn.dataset.deleteId))
  );
}