let toastTimer = null;

export function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  toast.innerText = message;
  toast.className = `fixed bottom-6 right-6 z-[110] max-w-sm px-4 py-3 rounded-xl text-sm font-medium shadow-lift ${
    type === "error" ? "bg-danger text-white" : "bg-rail text-white"
  }`;
  toast.classList.remove("hidden");

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 4000);
}
