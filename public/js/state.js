export const state = { recurrences: [], oneOffs: [] };
export const today = new Date();
export const displayMonth = { year: today.getFullYear(), monthIndex: today.getMonth() };

export function referenceMonth() {
  return { year: today.getFullYear(), monthIndex: today.getMonth() };
}