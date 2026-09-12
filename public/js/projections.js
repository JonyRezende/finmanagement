import { daysInMonth, monthKeyFor, monthOffset, yearMonthAdd } from "./calendar.js";

export function effectiveStartMonth(rec) {
  if (rec.startMonth) return rec.startMonth;
  if (rec.date) {
    const d = new Date(rec.date + "T00:00:00");
    return monthKeyFor(d.getFullYear(), d.getMonth());
  }
  return null;
}

export function isRecurrenceActiveInMonth(rec, year, monthIndex, refYear, refMonthIndex) {
  const key = monthKeyFor(year, monthIndex);
  const startMonth = effectiveStartMonth(rec);
  if (startMonth && key < startMonth) return false;
  if (rec.endMonth && key > rec.endMonth) return false;
  const offset = monthOffset(refYear, refMonthIndex, year, monthIndex);
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

function getMonthOverride(rec, key) {
  return rec.overrides?.[key];
}

export function getMonthTransactions(recurrences, oneOffs, year, monthIndex, refYear, refMonthIndex) {
  const items = [];
  const key = monthKeyFor(year, monthIndex);
  for (const rec of recurrences) {
    if (!isRecurrenceActiveInMonth(rec, year, monthIndex, refYear, refMonthIndex)) continue;
    const ov = getMonthOverride(rec, key);
    const description = ov?.description ?? rec.description;
    const type = ov?.type ?? rec.type;
    const amount = Number(ov?.amount ?? rec.amount);
    const dayRaw = ov?.day ?? rec.day;
    const day = Math.min(Number(dayRaw) || 1, daysInMonth(year, monthIndex));
    let installmentLabel = null;
    if (rec.hasInstallments) {
      const installmentNumber = Number(rec.installmentCurrent) + monthOffset(refYear, refMonthIndex, year, monthIndex);
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
  for (const item of oneOffs) {
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

export function netChangeForOffset(recurrences, oneOffs, offset, refYear, refMonthIndex) {
  const { year, monthIndex } = yearMonthAdd(refYear, refMonthIndex, offset);
  return getMonthTransactions(recurrences, oneOffs, year, monthIndex, refYear, refMonthIndex).reduce(
    (sum, t) => sum + (t.type === "income" ? t.amount : -t.amount),
    0
  );
}

export function earliestDataOffset(recurrences, oneOffs, refYear, refMonthIndex) {
  let min = 0;
  for (const rec of recurrences) {
    const startMonth = effectiveStartMonth(rec);
    if (!startMonth) continue;
    const [y, m] = startMonth.split("-").map(Number);
    const off = monthOffset(refYear, refMonthIndex, y, m - 1);
    if (off < min) min = off;
  }
  for (const item of oneOffs) {
    const d = new Date(item.date + "T00:00:00");
    const off = monthOffset(refYear, refMonthIndex, d.getFullYear(), d.getMonth());
    if (off < min) min = off;
  }
  return min;
}

export function balanceAtMonthStart(recurrences, oneOffs, offset, refYear, refMonthIndex) {
  const start = earliestDataOffset(recurrences, oneOffs, refYear, refMonthIndex);
  let bal = 0;
  for (let j = start; j < offset; j++) bal += netChangeForOffset(recurrences, oneOffs, j, refYear, refMonthIndex);
  return bal;
}

function addProjectionAmount(m, type, amount) {
  if (type === "income") m.income += amount;
  else m.expense += amount;
}

function buildMonthSkeleton(refYear, refMonthIndex, monthCount) {
  const months = [];
  for (let k = 0; k < monthCount; k++) {
    const d = new Date(refYear, refMonthIndex + k, 1);
    months.push({ year: d.getFullYear(), monthIndex: d.getMonth(), income: 0, expense: 0 });
  }
  return months;
}

function applyRecurrencesToMonths(recurrences, months, refYear, refMonthIndex) {
  for (const rec of recurrences) {
    for (const m of months) {
      if (!isRecurrenceActiveInMonth(rec, m.year, m.monthIndex, refYear, refMonthIndex)) continue;
      addProjectionAmount(m, rec.type, Number(rec.amount));
    }
  }
}

function applyOneOffsToMonths(oneOffs, months) {
  for (const item of oneOffs) {
    const d = new Date(item.date + "T00:00:00");
    for (const m of months) {
      if (d.getFullYear() !== m.year || d.getMonth() !== m.monthIndex) continue;
      addProjectionAmount(m, item.type, Number(item.amount));
    }
  }
}

function monthLabel(m) {
  const labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  return `${labels[m.monthIndex]}/${String(m.year).slice(2)}`;
}

function finalizeMonths(months, startBalance) {
  let balance = startBalance;
  for (const m of months) {
    m.net = m.income - m.expense;
    balance += m.net;
    m.endBalance = balance;
    m.label = monthLabel(m);
  }
  return months;
}

export function computeProjection(recurrences, oneOffs, refYear, refMonthIndex, monthCount = 7) {
  const startBalance = balanceAtMonthStart(recurrences, oneOffs, 0, refYear, refMonthIndex);
  const months = buildMonthSkeleton(refYear, refMonthIndex, monthCount);
  applyRecurrencesToMonths(recurrences, months, refYear, refMonthIndex);
  applyOneOffsToMonths(oneOffs, months);
  return finalizeMonths(months, startBalance);
}