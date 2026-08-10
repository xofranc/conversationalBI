import { MAX_TABLE_ROWS } from "../config/constants.js";

export function renderTable(res) {
  const tHead = document.getElementById("table-head");
  const tBody = document.getElementById("table-body");
  if (!tHead || !tBody) return;

  tHead.innerHTML = "";
  tBody.innerHTML = "";

  const cols = res.columns?.length
    ? res.columns.map((c) => c.name)
    : Object.keys(res.data?.[0] || {});
  const rows = res.data.slice(0, MAX_TABLE_ROWS);

  const numericCols = new Set(
    cols.filter(
      (col) =>
        rows.length > 0 &&
        rows.every(
          (r) =>
            r[col] === null ||
            r[col] === undefined ||
            typeof r[col] === "number",
        ),
    ),
  );

  cols.forEach((col) => {
    const th = document.createElement("th");
    th.className = `px-5 py-3 font-medium${numericCols.has(col) ? " text-right" : ""}`;
    th.innerText = col;
    tHead.appendChild(th);
  });

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    cols.forEach((col) => {
      const td = document.createElement("td");
      const isNum = numericCols.has(col);
      td.className = `px-5 py-3 whitespace-nowrap font-mono text-[0.8rem] tabular-nums${isNum ? " text-right" : ""}`;
      const val = row[col];
      td.innerText =
        val === null || val === undefined
          ? "—"
          : isNum
            ? Number(val).toLocaleString("es-CO")
            : val;
      tr.appendChild(td);
    });
    tBody.appendChild(tr);
  });
}
