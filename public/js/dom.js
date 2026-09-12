export function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

const SVG_NS = "http://www.w3.org/2000/svg";
export function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

export function showTooltip(tooltip, container, evt, text) {
  const rect = container.getBoundingClientRect();
  tooltip.textContent = text;
  tooltip.style.left = `${evt.clientX - rect.left + 12}px`;
  tooltip.style.top = `${evt.clientY - rect.top - 10}px`;
  tooltip.classList.remove("hidden");
}