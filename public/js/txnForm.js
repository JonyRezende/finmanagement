import { state, displayMonth, referenceMonth } from "./state.js";
import { daysInMonth, monthKeyFor, monthBefore, monthOffset } from "./calendar.js";
import { uid, formatAmountForInput, parseAmountInput } from "./money.js";
import { saveData } from "./api.js";
import { render } from "./render.js";

let editScope = null;
let editMonthKey = null;
let pendingEditId = null;

function showTransactionForm() {
  document.getElementById("transactionForm").classList.remove("hidden");
}

function hideTransactionForm() {
  document.getElementById("transactionForm").classList.add("hidden");
}

function getCurrentDateForInput() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function resetTransactionForm() {
  const form = document.getElementById("transactionForm");
  form.reset();
  document.getElementById("txId").value = "";
  document.getElementById("txKind").value = "oneoff";
  document.getElementById("txDate").value = getCurrentDateForInput();
  document.getElementById("txRecurring").checked = false;
  document.getElementById("recurringFields").classList.add("hidden");
  document.getElementById("installmentFields").classList.add("hidden");
  const submitBtn = document.getElementById("txSubmitBtn");
  submitBtn.title = "Adicionar";
  submitBtn.setAttribute("aria-label", "Adicionar");
  editScope = null;
  editMonthKey = null;
  pendingEditId = null;
}

function maskAmountOnInput(e) {
  const digits = e.target.value.replace(/\D/g, "");
  e.target.value = digits ? formatAmountForInput(Number(digits) / 100) : "";
}

function handleEditClick(kind, id) {
  if (kind === "recurrence") {
    pendingEditId = id;
    document.getElementById("editScopeModal").classList.remove("hidden");
  } else {
    editScope = null;
    editMonthKey = null;
    startEditTransaction(kind, id);
  }
}

function startEditTransaction(kind, id) {
  showTransactionForm();
  document.getElementById("txId").value = id;
  document.getElementById("txKind").value = kind;
  const submitBtn = document.getElementById("txSubmitBtn");
  submitBtn.title = "Salvar edição";
  submitBtn.setAttribute("aria-label", "Salvar edição");

  if (kind === "recurrence") {
    const rec = state.recurrences.find((r) => r.id === id);
    if (!rec) return;
    const ov = (rec.overrides && editMonthKey && rec.overrides[editMonthKey]) || null;
    const description = ov?.description ?? rec.description;
    const type = ov?.type ?? rec.type;
    const amount = ov?.amount ?? rec.amount;
    const day = ov?.day ?? rec.day;
    const [y, m] = (editMonthKey || rec.startMonth || monthKeyFor(displayMonth.year, displayMonth.monthIndex)).split("-").map(Number);
    const clampedDay = Math.min(Number(day) || 1, daysInMonth(y, m - 1));
    const dateStr = `${y}-${String(m).padStart(2, "0")}-${String(clampedDay).padStart(2, "0")}`;

    document.getElementById("txDescription").value = description;
    document.getElementById("txType").value = type;
    document.getElementById("txAmount").value = formatAmountForInput(amount);
    document.getElementById("txRecurring").checked = true;
    document.getElementById("recurringFields").classList.remove("hidden");
    document.getElementById("txDate").value = dateStr;
    document.getElementById("txHasInstallments").checked = !!rec.hasInstallments;
    document.getElementById("installmentFields").classList.toggle("hidden", !rec.hasInstallments);
    document.getElementById("txInstallmentCurrent").value = rec.installmentCurrent || "";
    document.getElementById("txInstallmentTotal").value = rec.installmentTotal || "";
  } else {
    const item = state.oneOffs.find((o) => o.id === id);
    if (!item) return;
    document.getElementById("txDescription").value = item.description;
    document.getElementById("txType").value = item.type;
    document.getElementById("txAmount").value = formatAmountForInput(item.amount);
    document.getElementById("txRecurring").checked = false;
    document.getElementById("recurringFields").classList.add("hidden");
    document.getElementById("txDate").value = item.date;
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function deleteTransaction(kind, id) {
  if (kind === "recurrence") {
    if (!confirm("Excluir esta recorrência vai remover todas as ocorrências futuras dela. Continuar?")) return;
    state.recurrences = state.recurrences.filter((r) => r.id !== id);
  } else {
    state.oneOffs = state.oneOffs.filter((o) => o.id !== id);
  }
  saveData();
  render();
}

function handleSubmit(e) {
  e.preventDefault();

  const id = document.getElementById("txId").value || uid();
  const isRecurring = document.getElementById("txRecurring").checked;
  const description = document.getElementById("txDescription").value.trim();
  const type = document.getElementById("txType").value;
  const amount = parseAmountInput(document.getElementById("txAmount").value);
  const date = document.getElementById("txDate").value;
  const previousKind = document.getElementById("txKind").value;

  if (!date) {
    alert("Selecione a data.");
    return;
  }

  // Se o tipo (recorrente/avulsa) mudou durante uma edição, remove do lugar antigo.
  if (previousKind === "recurrence" && !isRecurring) {
    state.recurrences = state.recurrences.filter((r) => r.id !== id);
  } else if (previousKind === "oneoff" && isRecurring) {
    state.oneOffs = state.oneOffs.filter((o) => o.id !== id);
  }

  if (isRecurring) {
    const hasInstallments = document.getElementById("txHasInstallments").checked;
    if (hasInstallments) {
      const c = Number(document.getElementById("txInstallmentCurrent").value);
      const t = Number(document.getElementById("txInstallmentTotal").value);
      if (!c || !t || c < 1 || t < 1) {
        alert("Preencha a parcela atual e o total de parcelas.");
        return;
      }
    }
    const day = new Date(date + "T00:00:00").getDate();
    const dateObj = new Date(date + "T00:00:00");
    const thisMonthKey = monthKeyFor(dateObj.getFullYear(), dateObj.getMonth());

    if (previousKind === "recurrence" && editScope === "single") {
      const rec = state.recurrences.find((r) => r.id === id);
      if (rec) {
        rec.overrides = rec.overrides || {};
        rec.overrides[editMonthKey] = { description, type, amount, day };
      }
    } else if (previousKind === "recurrence" && editScope === "future") {
      const rec = state.recurrences.find((r) => r.id === id);
      if (rec) {
        rec.endMonth = monthBefore(editMonthKey);
        let newCurrent = hasInstallments ? Number(document.getElementById("txInstallmentCurrent").value) : null;
        if (hasInstallments && rec.hasInstallments) {
          const ref = referenceMonth();
          const [ey, em] = editMonthKey.split("-").map(Number);
          newCurrent = Number(rec.installmentCurrent) + monthOffset(ref.year, ref.monthIndex, ey, em - 1);
        }
        state.recurrences.push({
          id: uid(),
          description,
          type,
          amount,
          date,
          day,
          startMonth: editMonthKey,
          endMonth: null,
          overrides: {},
          hasInstallments,
          installmentCurrent: newCurrent,
          installmentTotal: hasInstallments ? Number(document.getElementById("txInstallmentTotal").value) : null,
        });
      }
    } else {
      const rec = {
        id,
        description,
        type,
        amount,
        date,
        day,
        startMonth: thisMonthKey,
        endMonth: null,
        overrides: {},
        hasInstallments,
        installmentCurrent: hasInstallments ? Number(document.getElementById("txInstallmentCurrent").value) : null,
        installmentTotal: hasInstallments ? Number(document.getElementById("txInstallmentTotal").value) : null,
      };
      const idx = state.recurrences.findIndex((r) => r.id === id);
      if (idx >= 0) state.recurrences[idx] = rec;
      else state.recurrences.push(rec);
    }
  } else {
    const oneOff = {
      id,
      description,
      type,
      amount,
      date,
    };
    const idx = state.oneOffs.findIndex((o) => o.id === id);
    if (idx >= 0) state.oneOffs[idx] = oneOff;
    else state.oneOffs.push(oneOff);
  }

  saveData();
  resetTransactionForm();
  hideTransactionForm();
  render();
}

export function wireTxnForm() {
  document.getElementById("txAmount").addEventListener("input", maskAmountOnInput);

  document.getElementById("txRecurring").addEventListener("change", (e) => {
    document.getElementById("recurringFields").classList.toggle("hidden", !e.target.checked);
  });

  document.getElementById("editScopeSingleBtn").addEventListener("click", () => {
    editScope = "single";
    editMonthKey = monthKeyFor(displayMonth.year, displayMonth.monthIndex);
    document.getElementById("editScopeModal").classList.add("hidden");
    startEditTransaction("recurrence", pendingEditId);
  });

  document.getElementById("editScopeFutureBtn").addEventListener("click", () => {
    editScope = "future";
    editMonthKey = monthKeyFor(displayMonth.year, displayMonth.monthIndex);
    document.getElementById("editScopeModal").classList.add("hidden");
    startEditTransaction("recurrence", pendingEditId);
  });

  document.getElementById("editScopeCancelBtn").addEventListener("click", () => {
    pendingEditId = null;
    document.getElementById("editScopeModal").classList.add("hidden");
  });

  document.getElementById("txHasInstallments").addEventListener("change", (e) => {
    document.getElementById("installmentFields").classList.toggle("hidden", !e.target.checked);
  });

  document.getElementById("transactionForm").addEventListener("submit", handleSubmit);
}

export { handleEditClick, deleteTransaction, resetTransactionForm, showTransactionForm, hideTransactionForm };