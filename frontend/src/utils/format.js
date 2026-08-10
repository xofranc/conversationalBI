export function formatFolio() {
  const now = new Date();
  const fecha = now.toLocaleDateString("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const hora = now.toLocaleTimeString("es-CO", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `actualizado ${fecha} · ${hora}`;
}

export function formatDate(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  return d.toLocaleDateString("es-CO", { month: "short", year: "numeric" });
}

export function parseDrfError(err) {
  if (!err.data || typeof err.data !== "object") return null;
  const keys = Object.keys(err.data);
  if (!keys.length) return null;
  const first = err.data[keys[0]];
  return Array.isArray(first) ? first[0] : String(first);
}
