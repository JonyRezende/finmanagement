import { state } from "./state.js";
import { render } from "./render.js";

export async function loadData() {
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

export async function saveData() {
  await fetch("/api/data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
}