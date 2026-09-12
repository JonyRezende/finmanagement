export function fmtMoney(n) {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatAmountForInput(n) {
  return (Number(n) || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function parseAmountInput(str) {
  const digits = String(str).replace(/\D/g, "");
  return digits ? Number(digits) / 100 : 0;
}

export function uid() {
  return crypto.randomUUID().replaceAll("-", "");
}