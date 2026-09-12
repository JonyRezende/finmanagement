import { fmtMoney } from "./money.js";
import { svgEl, showTooltip } from "./dom.js";

export function renderProjectionTable(months) {
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

export function renderBarChart(months) {
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

export function renderLineChart(months) {
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