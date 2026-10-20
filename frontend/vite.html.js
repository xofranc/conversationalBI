import fs from "node:fs";
import path from "node:path";

const INCLUDE_RE = /<!--\s*@include:?\s+([^\s>]+)\s*-->/g;
const PAGE_ROUTES = {
  "/app.html": "/pages/app.html",
  "/roadmap.html": "/pages/roadmap.html",
};

/**
 * Las páginas viven en `pages/` y se componen de parciales en
 * `src/interfaces/views/`. Este plugin:
 *   1. expone /app.html y /roadmap.html en dev (sin cambiar la URL pública),
 *   2. expande los `<!-- @include: ruta -->` en dev y build,
 *   3. aplana la salida del build para que nginx siga sirviendo en la raíz.
 */
export function htmlPages() {
  let root = process.cwd();

  const expand = (html, filename, seen = new Set()) =>
    html.replace(INCLUDE_RE, (_match, relative) => {
      const file = path.resolve(path.dirname(filename), relative);
      if (seen.has(file)) {
        throw new Error(`Include circular: ${file}`);
      }
      if (!fs.existsSync(file)) {
        throw new Error(`Include no encontrado: ${relative} (desde ${filename})`);
      }
      const content = fs.readFileSync(file, "utf8");
      return expand(content, file, new Set([...seen, file]));
    });

  return {
    name: "cbi-html-pages",
    configResolved(config) {
      root = config.root;
    },
    transformIndexHtml: {
      order: "pre",
      handler(html, ctx) {
        return expand(html, ctx.filename);
      },
    },
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        if (!req.url) return next();
        const [pathname, query] = req.url.split("?");
        if (PAGE_ROUTES[pathname]) {
          req.url = `${PAGE_ROUTES[pathname]}${query ? `?${query}` : ""}`;
        }
        next();
      });
      server.watcher.add(path.join(root, "src/interfaces/views"));
    },
    handleHotUpdate(ctx) {
      if (ctx.file.includes("/interfaces/views/") && ctx.file.endsWith(".html")) {
        ctx.server.ws.send({ type: "full-reload" });
        return [];
      }
      return undefined;
    },
    closeBundle() {
      const outDir = path.resolve(root, "dist");
      for (const page of ["app.html", "roadmap.html"]) {
        const from = path.join(outDir, "pages", page);
        const to = path.join(outDir, page);
        if (fs.existsSync(from)) fs.copyFileSync(from, to);
      }
    },
  };
}
