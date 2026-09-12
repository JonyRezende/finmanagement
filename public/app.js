const state = {
  recurrences: [],
  oneOffs: [],
};

const MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const MONTH_LABELS_FULL = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

const today = new Date();
const displayMonth = { year: today.getFullYear(), monthIndex: today.getMonth() };

function fmtMoney(n) {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatAmountForInput(n) {
  return (Number(n) || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function parseAmountInput(str) {
  const digits = String(str).replace(/\D/g, "");
  return digits ? Number(digits) / 100 : 0;
}

function maskAmountOnInput(e) {
  const digits = e.target.value.replace(/\D/g, "");
  e.target.value = digits ? formatAmountForInput(Number(digits) / 100) : "";
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function daysInMonth(year, monthIndex) {
  return new Date(year, monthIndex + 1, 0).getDate();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadData() {
  const res = await fetch("/api/data");
  if (res.status === 401) {
    window.location.href = "/login.html";
    return;
  }
  const json = await res.json();
  state.recurrences = json.recurrences || [];
  state.oneOffs = json.oneOffs || [];
  render();
}

async function saveData() {
  await fetch("/api/data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
}

function render() {
  renderProjection();
  renderExtrato();
}

// ---------- Extrato mensal (listagem única: recorrentes + avulsas) ----------

function referenceMonth() {
  return { year: today.getFullYear(), monthIndex: today.getMonth() };
}

function monthOffset(year, monthIndex) {
  const ref = referenceMonth();
  return (year - ref.year) * 12 + (monthIndex - ref.monthIndex);
}

function yearMonthForOffset(offset) {
  const ref = referenceMonth();
  const total = ref.year * 12 + ref.monthIndex + offset;
  return { year: Math.floor(total / 12), monthIndex: ((total % 12) + 12) % 12 };
}

function monthKeyFor(year, monthIndex) {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}`;
}

function monthBefore(key) {
  const [y, m] = key.split("-").map(Number);
  const d = new Date(y, m - 2, 1);
  return monthKeyFor(d.getFullYear(), d.getMonth());
}

function effectiveStartMonth(rec) {
  if (rec.startMonth) return rec.startMonth;
  if (rec.date) {
    const d = new Date(rec.date + "T00:00:00");
    return monthKeyFor(d.getFullYear(), d.getMonth());
  }
  return null;
}

function isRecurrenceActiveInMonth(rec, year, monthIndex) {
  const key = monthKeyFor(year, monthIndex);
  const startMonth = effectiveStartMonth(rec);
  if (startMonth && key < startMonth) return false;
  if (rec.endMonth && key > rec.endMonth) return false;
  const offset = monthOffset(year, monthIndex);
  if (rec.hasInstallments) {
    const total = Number(rec.installmentTotal);
    const current = Number(rec.installmentCurrent);
    if (!total || !current) return false;
    const installmentNumber = current + offset;
    return installmentNumber >= 1 && installmentNumber <= total;
  }
  if (rec.endDate) {
    const end = new Date(rec.endDate + "T00:00:00");
    const monthEnd = new Date(year, monthIndex, daysInMonth(year, monthIndex));
    return monthEnd <= end;
  }
  return true;
}

function getMonthTransactions(year, monthIndex) {
  const items = [];
  const key = monthKeyFor(year, monthIndex);
  for (const rec of state.recurrences) {
    if (!isRecurrenceActiveInMonth(rec, year, monthIndex)) continue;
    const ov = rec.overrides && rec.overrides[key];
    const description = ov?.description ?? rec.description;
    const type = ov?.type ?? rec.type;
    const amount = Number(ov?.amount ?? rec.amount);
    const dayRaw = ov?.day ?? rec.day;
    const day = Math.min(Number(dayRaw) || 1, daysInMonth(year, monthIndex));
    let installmentLabel = null;
    if (rec.hasInstallments) {
      const installmentNumber = Number(rec.installmentCurrent) + monthOffset(year, monthIndex);
      installmentLabel = `${installmentNumber}/${Number(rec.installmentTotal)}`;
    }
    items.push({
      id: rec.id,
      kind: "recurrence",
      date: new Date(year, monthIndex, day),
      description,
      type,
      amount,
      installmentLabel,
    });
  }
  for (const item of state.oneOffs) {
    const d = new Date(item.date + "T00:00:00");
    if (d.getFullYear() === year && d.getMonth() === monthIndex) {
      items.push({
        id: item.id,
        kind: "oneoff",
        date: d,
        description: item.description,
        type: item.type,
        amount: Number(item.amount),
      });
    }
  }
  items.sort((a, b) => a.date - b.date);
  return items;
}

function netChangeForOffset(offset) {
  const { year, monthIndex } = yearMonthForOffset(offset);
  return getMonthTransactions(year, monthIndex).reduce(
    (sum, t) => sum + (t.type === "income" ? t.amount : -t.amount),
    0
  );
}

function earliestDataOffset() {
  let min = 0;
  for (const rec of state.recurrences) {
    const startMonth = effectiveStartMonth(rec);
    if (!startMonth) continue;
    const [y, m] = startMonth.split("-").map(Number);
    const off = monthOffset(y, m - 1);
    if (off < min) min = off;
  }
  for (const item of state.oneOffs) {
    const d = new Date(item.date + "T00:00:00");
    const off = monthOffset(d.getFullYear(), d.getMonth());
    if (off < min) min = off;
  }
  return min;
}

function balanceAtMonthStart(offset) {
  const start = earliestDataOffset();
  let bal = 0;
  for (let j = start; j < offset; j++) bal += netChangeForOffset(j);
  return bal;
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function renderExtrato() {
  document.getElementById("monthLabel").textContent = `${MONTH_LABELS_FULL[displayMonth.monthIndex]}/${displayMonth.year}`;

  const offset = monthOffset(displayMonth.year, displayMonth.monthIndex);
  const startBalance = balanceAtMonthStart(offset);
  const transactions = getMonthTransactions(displayMonth.year, displayMonth.monthIndex);

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

// ---------- Formulário único de transação (recorrente ou avulsa) ----------

function showTransactionForm() {
  document.getElementById("transactionForm").classList.remove("hidden");
}

function hideTransactionForm() {
  document.getElementById("transactionForm").classList.add("hidden");
}

let editScope = null;
let editMonthKey = null;
let pendingEditId = null;

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

// ---------- Projeção ----------

function computeProjection() {
  const months = [];
  for (let k = 0; k < 7; k++) {
    const d = new Date(today.getFullYear(), today.getMonth() + k, 1);
    months.push({ year: d.getFullYear(), monthIndex: d.getMonth(), income: 0, expense: 0 });
  }

  for (const rec of state.recurrences) {
    for (let k = 0; k < months.length; k++) {
      const m = months[k];
      if (isRecurrenceActiveInMonth(rec, m.year, m.monthIndex)) {
        if (rec.type === "income") m.income += Number(rec.amount);
        else m.expense += Number(rec.amount);
      }
    }
  }

  for (const item of state.oneOffs) {
    const d = new Date(item.date + "T00:00:00");
    for (const m of months) {
      if (d.getFullYear() === m.year && d.getMonth() === m.monthIndex) {
        if (item.type === "income") m.income += Number(item.amount);
        else m.expense += Number(item.amount);
      }
    }
  }

  let balance = balanceAtMonthStart(0);
  for (const m of months) {
    m.net = m.income - m.expense;
    balance += m.net;
    m.endBalance = balance;
    m.label = `${MONTH_LABELS[m.monthIndex]}/${String(m.year).slice(2)}`;
  }
  return months;
}

function renderProjection() {
  const months = computeProjection();
  renderProjectionTable(months);
  renderBarChart(months);
  renderLineChart(months);
}

function renderProjectionTable(months) {
  const body = document.getElementById("projectionTableBody");
  body.innerHTML = "";
  for (const m of months) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${m.label}</td>
      <td class="amount-income">${fmtMoney(m.income)}</td>
      <td class="amount-expense">${fmtMoney(m.expense)}</td>
      <td>${fmtMoney(m.endBalance)}</td>`;
    body.appendChild(tr);
  }
}

const SVG_NS = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

function renderBarChart(months) {
  const host = document.getElementById("barChart");
  host.innerHTML = "";

  const legend = document.createElement("div");
  legend.className = "viz-legend";
  legend.innerHTML = `
    <span class="viz-legend-item"><span class="viz-legend-swatch" style="background:var(--series-income)"></span>Entradas</span>
    <span class="viz-legend-item"><span class="viz-legend-swatch" style="background:var(--series-expense)"></span>Saídas</span>`;
  host.appendChild(legend);

  const wrap = document.createElement("div");
  wrap.className = "chart-svg-wrap";
  host.appendChild(wrap);

  const width = wrap.parentElement.parentElement.clientWidth || 900;
  const height = 220;
  const padding = { top: 10, right: 10, bottom: 26, left: 10 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const maxVal = Math.max(1, ...months.map((m) => Math.max(m.income, m.expense)));
  const groupW = plotW / months.length;
  const barW = Math.min(22, groupW / 3.2);

  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width: "100%", height, role: "img" });

  svg.appendChild(
    svgEl("line", {
      x1: padding.left,
      x2: width - padding.right,
      y1: height - padding.bottom,
      y2: height - padding.bottom,
      stroke: "var(--grid)",
      "stroke-width": 1,
    })
  );

  const tooltip = document.createElement("div");
  tooltip.className = "viz-tooltip hidden";
  wrap.appendChild(tooltip);

  months.forEach((m, i) => {
    const cx = padding.left + groupW * i + groupW / 2;
    const incomeH = (m.income / maxVal) * plotH;
    const expenseH = (m.expense / maxVal) * plotH;

    const incomeBar = svgEl("rect", {
      x: cx - barW - 3,
      y: height - padding.bottom - incomeH,
      width: barW,
      height: Math.max(incomeH, 1),
      rx: 4,
      fill: "var(--series-income)",
    });
    const expenseBar = svgEl("rect", {
      x: cx + 3,
      y: height - padding.bottom - expenseH,
      width: barW,
      height: Math.max(expenseH, 1),
      rx: 4,
      fill: "var(--series-expense)",
    });

    [
      [incomeBar, "Entradas", m.income],
      [expenseBar, "Saídas", m.expense],
    ].forEach(([bar, label, value]) => {
      bar.addEventListener("mousemove", (evt) => {
        showTooltip(tooltip, wrap, evt, `${m.label} — ${label}: ${fmtMoney(value)}`);
      });
      bar.addEventListener("mouseleave", () => tooltip.classList.add("hidden"));
    });

    svg.appendChild(incomeBar);
    svg.appendChild(expenseBar);

    const label = svgEl("text", {
      x: cx,
      y: height - padding.bottom + 16,
      "text-anchor": "middle",
      fill: "var(--text-secondary)",
      "font-size": "11",
    });
    label.textContent = m.label;
    svg.appendChild(label);
  });

  wrap.appendChild(svg);
}

function renderLineChart(months) {
  const host = document.getElementById("lineChart");
  host.innerHTML = "";

  const wrap = document.createElement("div");
  wrap.className = "chart-svg-wrap";
  host.appendChild(wrap);

  const width = wrap.parentElement.parentElement.clientWidth || 900;
  const height = 220;
  const padding = { top: 20, right: 60, bottom: 26, left: 10 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const values = months.map((m) => m.endBalance);
  const minVal = Math.min(0, ...values);
  const maxVal = Math.max(1, ...values);
  const range = maxVal - minVal || 1;

  const stepX = plotW / (months.length - 1);
  const points = months.map((m, i) => {
    const x = padding.left + stepX * i;
    const y = padding.top + plotH - ((m.endBalance - minVal) / range) * plotH;
    return { x, y, m };
  });

  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, width: "100%", height, role: "img" });

  const zeroY = padding.top + plotH - ((0 - minVal) / range) * plotH;
  svg.appendChild(
    svgEl("line", {
      x1: padding.left,
      x2: width - padding.right,
      y1: zeroY,
      y2: zeroY,
      stroke: "var(--grid)",
      "stroke-width": 1,
    })
  );

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  svg.appendChild(
    svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: "var(--series-balance)",
      "stroke-width": 2,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    })
  );

  const tooltip = document.createElement("div");
  tooltip.className = "viz-tooltip hidden";
  wrap.appendChild(tooltip);

  points.forEach((p, i) => {
    const dot = svgEl("circle", { cx: p.x, cy: p.y, r: 4, fill: "var(--series-balance)" });
    dot.addEventListener("mousemove", (evt) =>
      showTooltip(tooltip, wrap, evt, `${p.m.label}: ${fmtMoney(p.m.endBalance)}`)
    );
    dot.addEventListener("mouseleave", () => tooltip.classList.add("hidden"));
    svg.appendChild(dot);

    const label = svgEl("text", {
      x: p.x,
      y: height - padding.bottom + 16,
      "text-anchor": "middle",
      fill: "var(--text-secondary)",
      "font-size": "11",
    });
    label.textContent = p.m.label;
    svg.appendChild(label);

    if (i === points.length - 1) {
      const endLabel = svgEl("text", {
        x: p.x + 6,
        y: p.y + 4,
        "text-anchor": "start",
        fill: "var(--series-balance)",
        "font-size": "11",
        "font-weight": "600",
      });
      endLabel.textContent = fmtMoney(p.m.endBalance);
      svg.appendChild(endLabel);
    }
  });

  wrap.appendChild(svg);
}

function showTooltip(tooltip, container, evt, text) {
  const rect = container.getBoundingClientRect();
  tooltip.textContent = text;
  tooltip.style.left = `${evt.clientX - rect.left + 12}px`;
  tooltip.style.top = `${evt.clientY - rect.top - 10}px`;
  tooltip.classList.remove("hidden");
}

// ---------- Event wiring ----------

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

document.getElementById("transactionForm").addEventListener("submit", (e) => {
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
          const [ey, em] = editMonthKey.split("-").map(Number);
          newCurrent = Number(rec.installmentCurrent) + monthOffset(ey, em - 1);
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

const calculator = { display: "0", expression: "", operand: null, operator: null, waitingForNext: false };

function renderCalculator() {
  document.getElementById("calculatorDisplay").textContent = calculator.display;
  document.getElementById("calculatorExpression").textContent = calculator.expression;
  document.querySelectorAll('[data-calc="operator"]').forEach((button) => {
    button.classList.toggle("is-active", button.dataset.value === calculator.operator);
  });
}

function calculatorNumber() {
  return Number(calculator.display.replace(",", "."));
}

function calculatorResult(left, right, operator) {
  if (operator === "+") return left + right;
  if (operator === "-") return left - right;
  if (operator === "*") return left * right;
  if (operator === "/") return right === 0 ? null : left / right;
  return right;
}

function calculatorOperatorLabel(operator) {
  return { "/": "÷", "*": "×" }[operator] || operator;
}

function setCalculatorResult(result) {
  calculator.display = result === null || !Number.isFinite(result)
    ? "Erro"
    : String(Number(result.toFixed(10))).replace(".", ",");
}

document.querySelectorAll("[data-calc]").forEach((button) => {
  button.addEventListener("click", () => {
    const action = button.dataset.calc;
    const value = button.dataset.value;

    if (action === "clear") {
      Object.assign(calculator, { display: "0", expression: "", operand: null, operator: null, waitingForNext: false });
    } else if (action === "backspace") {
      if (!calculator.waitingForNext && calculator.display !== "Erro") {
        calculator.display = calculator.display.length > 1 ? calculator.display.slice(0, -1) : "0";
        if (calculator.operator) calculator.expression = `${calculator.operand} ${calculatorOperatorLabel(calculator.operator)} ${calculator.display}`;
      }
    } else if (action === "digit") {
      if (calculator.waitingForNext || calculator.display === "Erro") {
        calculator.display = value;
        calculator.waitingForNext = false;
        if (!calculator.operator) calculator.expression = "";
      } else {
        calculator.display = calculator.display === "0" ? value : calculator.display + value;
      }
      if (calculator.operator) calculator.expression = `${calculator.operand} ${calculatorOperatorLabel(calculator.operator)} ${calculator.display}`;
    } else if (action === "decimal") {
      if (calculator.waitingForNext || calculator.display === "Erro") {
        calculator.display = "0,";
        calculator.waitingForNext = false;
        if (!calculator.operator) calculator.expression = "";
      } else if (!calculator.display.includes(",")) {
        calculator.display += ",";
      }
      if (calculator.operator) calculator.expression = `${calculator.operand} ${calculatorOperatorLabel(calculator.operator)} ${calculator.display}`;
    } else if (action === "operator") {
      const current = calculatorNumber();
      if (calculator.operator && !calculator.waitingForNext) {
        const result = calculatorResult(calculator.operand, current, calculator.operator);
        setCalculatorResult(result);
        calculator.operand = result;
      } else {
        calculator.operand = current;
      }
      calculator.operator = value;
      calculator.waitingForNext = true;
      calculator.expression = `${calculator.display} ${calculatorOperatorLabel(value)}`;
    } else if (action === "equals" && calculator.operator && !calculator.waitingForNext) {
      const expression = calculator.expression;
      const result = calculatorResult(calculator.operand, calculatorNumber(), calculator.operator);
      setCalculatorResult(result);
      calculator.expression = `${expression} =`;
      calculator.operand = null;
      calculator.operator = null;
      calculator.waitingForNext = true;
    }

    renderCalculator();
  });
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login.html";
});

loadData();
