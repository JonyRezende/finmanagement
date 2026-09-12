import { state, today } from "./state.js";
import { computeProjection } from "./projections.js";
import { renderProjectionTable, renderBarChart, renderLineChart } from "./charts.js";

export function renderProjection() {
  const months = computeProjection(state.recurrences, state.oneOffs, today.getFullYear(), today.getMonth());
  renderProjectionTable(months);
  renderBarChart(months);
  renderLineChart(months);
}