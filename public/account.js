const emailForm = document.getElementById("emailForm");
const passwordForm = document.getElementById("passwordForm");
const logoutLink = document.getElementById("logoutLink");
const emailEl = document.getElementById("accountEmail");

function setMessage(errorEl, successEl, text, ok) {
  errorEl.classList.toggle("hidden", ok || !text);
  errorEl.textContent = ok ? "" : text;
  successEl.classList.toggle("hidden", !ok || !text);
  successEl.textContent = ok ? text : "";
}

async function loadAccount() {
  const res = await fetch("/api/me");
  if (res.status === 401) {
    window.location.href = "/login.html";
    return;
  }
  const data = await res.json();
  emailEl.textContent = data.email;
}

emailForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setMessage(document.getElementById("emailError"), document.getElementById("emailSuccess"), "", true);

  const payload = {
    current_password: document.getElementById("emailPassword").value,
    new_email: document.getElementById("newEmail").value,
  };

  const res = await fetch("/api/account/email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    setMessage(document.getElementById("emailError"), document.getElementById("emailSuccess"), data.error || "Não foi possível atualizar.", false);
    return;
  }

  emailEl.textContent = data.email;
  emailForm.reset();
  setMessage(document.getElementById("emailError"), document.getElementById("emailSuccess"), "Email atualizado.", true);
});

passwordForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setMessage(document.getElementById("passwordError"), document.getElementById("passwordSuccess"), "", true);

  const current = document.getElementById("currentPassword").value;
  const next = document.getElementById("newPassword").value;
  const confirm = document.getElementById("newPasswordConfirm").value;

  if (next !== confirm) {
    setMessage(document.getElementById("passwordError"), document.getElementById("passwordSuccess"), "As senhas não coincidem.", false);
    return;
  }

  const res = await fetch("/api/account/password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: current, new_password: next }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    setMessage(document.getElementById("passwordError"), document.getElementById("passwordSuccess"), data.error || "Não foi possível atualizar.", false);
    return;
  }

  passwordForm.reset();
  setMessage(document.getElementById("passwordError"), document.getElementById("passwordSuccess"), "Senha atualizada.", true);
});

logoutLink.addEventListener("click", async (e) => {
  e.preventDefault();
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login.html";
});

loadAccount();