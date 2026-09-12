export const MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
export const MONTH_LABELS_FULL = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

export function daysInMonth(year, monthIndex) {
  return new Date(year, monthIndex + 1, 0).getDate();
}

export function monthKeyFor(year, monthIndex) {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}`;
}

export function monthBefore(key) {
  const [y, m] = key.split("-").map(Number);
  const d = new Date(y, m - 2, 1);
  return monthKeyFor(d.getFullYear(), d.getMonth());
}

export function monthOffset(refYear, refMonthIndex, year, monthIndex) {
  return (year - refYear) * 12 + (monthIndex - refMonthIndex);
}

export function yearMonthAdd(refYear, refMonthIndex, offset) {
  const total = refYear * 12 + refMonthIndex + offset;
  return { year: Math.floor(total / 12), monthIndex: ((total % 12) + 12) % 12 };
}