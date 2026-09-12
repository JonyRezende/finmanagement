let mode = "login"; // ou "register"

const form = document.getElementById("authForm");
const errorEl = document.getElementById("authError");
const toggleLink = document.getElementById("toggleModeLink");
const formTitle = document.getElementById("formTitle");
const submitBtn = document.getElementById("authSubmitBtn");
const confirmField = document.getElementById("authPasswordConfirmField");
const confirmInput = document.getElementById("authPasswordConfirm");

function applyMode() {
  if (mode === "login") {
    formTitle.textContent = "Entrar";
    submitBtn.textContent = "Entrar";
    toggleLink.textContent = "Não tem conta? Cadastre-se";
    confirmField.classList.add("hidden");
    confirmInput.required = false;
  } else {
    formTitle.textContent = "Criar conta";
    submitBtn.textContent = "Cadastrar";
    toggleLink.textContent = "Já tem conta? Entrar";
    confirmField.classList.remove("hidden");
    confirmInput.required = true;
  }
  errorEl.classList.add("hidden");
}

toggleLink.addEventListener("click", (e) => {
  e.preventDefault();
  mode = mode === "login" ? "register" : "login";
  applyMode();
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.classList.add("hidden");

  const email = document.getElementById("authEmail").value.trim();
  const password = document.getElementById("authPassword").value;

  if (mode === "register" && password !== confirmInput.value) {
    errorEl.textContent = "As senhas não coincidem.";
    errorEl.classList.remove("hidden");
    return;
  }

  const url = mode === "login" ? "/api/login" : "/api/register";

  const body = { email, password };
  if (mode === "register") {
    body.password_confirm = confirmInput.value;
  }

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    errorEl.textContent = data.error || "Não foi possível continuar.";
    errorEl.classList.remove("hidden");
    return;
  }

  window.location.href = "/index.html";
});

applyMode();
