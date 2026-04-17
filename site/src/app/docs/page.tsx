"use client";

import { useEffect, useRef, useState } from "react";

const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || "";
const SWAGGER_CSS_URL = `${BASE_PATH}/swagger-ui/swagger-ui.css`;
const SWAGGER_BUNDLE_URL = `${BASE_PATH}/swagger-ui/swagger-ui-bundle.js`;
const STATIC_SPEC_URL = `${BASE_PATH}/openapi.json`;
const LIVE_URL =
  process.env.NEXT_PUBLIC_BORG_API_URL
    ? `${process.env.NEXT_PUBLIC_BORG_API_URL}/openapi.json`
    : null;
const SWAGGER_CLIENT_ID = process.env.NEXT_PUBLIC_BORG_ENTRA_CLIENT_ID ?? "";
const SWAGGER_SCOPES = (
  process.env.NEXT_PUBLIC_BORG_ENTRA_SCOPES ?? ""
)
  .split(",")
  .map((scope) => scope.trim())
  .filter(Boolean);
const OAUTH_REDIRECT_URL =
  typeof window !== "undefined"
    ? `${window.location.origin}${BASE_PATH}/docs/oauth2-redirect`
    : `${BASE_PATH}/docs/oauth2-redirect`;

export default function Docs() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [oauthEnabled, setOauthEnabled] = useState(false);
  const [specSource, setSpecSource] = useState<"live" | "static" | null>(null);

  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = SWAGGER_CSS_URL;
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = SWAGGER_BUNDLE_URL;
    script.onload = () => initSwagger();
    script.onerror = () => setError("Failed to load local Swagger UI assets.");
    document.body.appendChild(script);

    return () => {
      document.head.removeChild(link);
      document.body.removeChild(script);
    };
  }, []);

  async function initSwagger() {
    // Try live API first, fall back to bundled static spec
    let specUrl = STATIC_SPEC_URL;
    let source: "live" | "static" = "static";

    if (LIVE_URL) {
      try {
        const res = await fetch(LIVE_URL, { method: "GET", signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          specUrl = LIVE_URL;
          source = "live";
        }
      } catch {
        // Live API not available — use static spec
      }
    }

    setSpecSource(source);

    try {
      // @ts-expect-error loaded from CDN
      const ui = window.SwaggerUIBundle({
        url: specUrl,
        dom_id: "#swagger-container",
        deepLinking: true,
        presets: [
          // @ts-expect-error loaded from CDN
          window.SwaggerUIBundle.presets.apis,
        ],
        layout: "BaseLayout",
        defaultModelsExpandDepth: 1,
        defaultModelExpandDepth: 2,
        docExpansion: "list",
        filter: true,
        tryItOutEnabled: source === "live",
        persistAuthorization: false,
        oauth2RedirectUrl: OAUTH_REDIRECT_URL,
        onComplete: () => setLoaded(true),
        onFailure: () => setError("Could not load OpenAPI schema."),
      });

      if (source === "live" && SWAGGER_CLIENT_ID) {
        ui.initOAuth({
          clientId: SWAGGER_CLIENT_ID,
          appName: "Borg Site Docs",
          usePkceWithAuthorizationCodeGrant: true,
          scopes: SWAGGER_SCOPES.join(" "),
        });
        setOauthEnabled(true);
      } else {
        setOauthEnabled(false);
      }
    } catch {
      setError("Failed to initialize Swagger UI.");
    }
  }

  return (
    <div className="pt-16">
      <div className="border-b border-[var(--border)] bg-gradient-to-b from-[var(--accent-blue)]/5 to-transparent">
        <div className="mx-auto max-w-6xl px-6 pb-8 pt-20">
          <h1 className="text-4xl font-extrabold text-[var(--text-primary)]">
            API Docs
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--text-secondary)]">
            Interactive OpenAPI documentation. When viewing on GitHub Pages, the
            bundled spec is displayed read-only. Run Borg locally to try
            endpoints interactively.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-xs text-[var(--text-muted)]">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 ${
                specSource === "live"
                  ? "border-[var(--accent-green)]/30 text-[var(--accent-green)]"
                  : "border-[var(--accent-amber)]/30 text-[var(--accent-amber)]"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  specSource === "live"
                    ? "bg-[var(--accent-green)]"
                    : "bg-[var(--accent-amber)]"
                }`}
              />
              {specSource === "live" ? "Connected to live API" : "Bundled spec (read-only)"}
            </span>
            {oauthEnabled && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--accent-blue)]/30 px-3 py-1 text-[var(--accent-blue)]">
                <span className="h-2 w-2 rounded-full bg-[var(--accent-blue)]" />
                Entra PKCE enabled
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">
            Need setup details?
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
            MCP setup, Codex, Claude Code, and Kiro examples, AGENTS.md guidance, Claude Desktop instructions,
            and generic use cases now live on the dedicated integrations page. This page stays focused
            on the live OpenAPI surface and interactive REST testing. Swagger UI assets are served locally
            by this site rather than loaded from a third-party CDN. The Borg backend must expose{" "}
            <code>/openapi.json</code> with <code>BORG_ENABLE_DOCS=true</code> for this page to
            function.
          </p>
          <div className="mt-5">
            <a
              href="/integrations"
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-accent)] px-5 py-3 text-sm font-semibold text-[var(--text-primary)] transition-all hover:border-[var(--accent-green)]/50 hover:bg-[var(--bg-primary)]"
            >
              Open Integrations
            </a>
          </div>
        </div>
      </div>

      {error && (
        <div className="mx-auto max-w-6xl px-6 py-8">
          <div className="rounded-xl border border-[var(--accent-red)]/30 bg-[var(--accent-red)]/5 p-6">
            <h3 className="mb-2 text-lg font-semibold text-[var(--accent-red)]">
              API Unavailable
            </h3>
            <p className="text-sm text-[var(--text-secondary)]">{error}</p>
          </div>
        </div>
      )}

      {!loaded && !error && (
        <div className="mx-auto max-w-6xl px-6 py-20 text-center">
          <div className="inline-flex items-center gap-3 text-[var(--text-muted)]">
            <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Loading OpenAPI schema...
          </div>
        </div>
      )}

      <div className="swagger-dark-override">
        <div
          id="swagger-container"
          ref={containerRef}
          className="mx-auto max-w-6xl px-6 py-6"
        />
      </div>

      <style jsx global>{`
        .swagger-dark-override .swagger-ui {
          font-family: "Inter", -apple-system, sans-serif;
        }
        .swagger-dark-override .swagger-ui,
        .swagger-dark-override .swagger-ui .scheme-container,
        .swagger-dark-override .swagger-ui .opblock-tag,
        .swagger-dark-override .swagger-ui section.models,
        .swagger-dark-override .swagger-ui .model-container {
          background: transparent;
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .info .title,
        .swagger-dark-override .swagger-ui .opblock-tag {
          color: #e2e8f0;
          border-bottom-color: #1e293b;
        }
        .swagger-dark-override .swagger-ui .info .description p,
        .swagger-dark-override .swagger-ui .info .description li,
        .swagger-dark-override .swagger-ui .markdown p,
        .swagger-dark-override .swagger-ui .markdown li,
        .swagger-dark-override .swagger-ui table thead tr th,
        .swagger-dark-override .swagger-ui table thead tr td,
        .swagger-dark-override .swagger-ui .response-col_description__inner p,
        .swagger-dark-override .swagger-ui .parameter__name,
        .swagger-dark-override .swagger-ui .parameter__type,
        .swagger-dark-override .swagger-ui label,
        .swagger-dark-override .swagger-ui .model-title,
        .swagger-dark-override .swagger-ui .model {
          color: #94a3b8;
        }
        .swagger-dark-override .swagger-ui .opblock {
          border-color: #1e293b;
          background: #111827;
        }
        .swagger-dark-override .swagger-ui .opblock .opblock-summary {
          border-bottom-color: #1e293b;
        }
        .swagger-dark-override .swagger-ui .opblock .opblock-summary-description {
          color: #94a3b8;
        }
        .swagger-dark-override .swagger-ui .opblock-body pre,
        .swagger-dark-override .swagger-ui .highlight-code {
          background: #0a0e17 !important;
          color: #e2e8f0;
          border-radius: 8px;
        }
        .swagger-dark-override .swagger-ui .opblock.opblock-post {
          border-color: #22c55e40;
          background: #22c55e08;
        }
        .swagger-dark-override .swagger-ui .opblock.opblock-post .opblock-summary {
          border-color: #22c55e30;
        }
        .swagger-dark-override .swagger-ui .opblock.opblock-get {
          border-color: #60a5fa40;
          background: #60a5fa08;
        }
        .swagger-dark-override .swagger-ui .opblock.opblock-get .opblock-summary {
          border-color: #60a5fa30;
        }
        .swagger-dark-override .swagger-ui .opblock.opblock-put {
          border-color: #fbbf2440;
          background: #fbbf2408;
        }
        .swagger-dark-override .swagger-ui .opblock.opblock-delete {
          border-color: #f8717140;
          background: #f8717108;
        }
        .swagger-dark-override .swagger-ui .btn {
          border-color: #334155;
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .btn:hover {
          background: #1a2332;
        }
        .swagger-dark-override .swagger-ui .btn.execute {
          background: #22c55e;
          border-color: #22c55e;
          color: #0a0e17;
        }
        .swagger-dark-override .swagger-ui input[type="text"],
        .swagger-dark-override .swagger-ui textarea,
        .swagger-dark-override .swagger-ui select {
          background: #0a0e17;
          border-color: #334155;
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui section.models {
          border-color: #1e293b;
        }
        .swagger-dark-override .swagger-ui section.models .model-box {
          background: #111827;
        }
        .swagger-dark-override .swagger-ui .model-toggle::after {
          filter: invert(1);
        }
        .swagger-dark-override .swagger-ui .info .description pre {
          background: #0a0e17 !important;
          border: 1px solid #1e293b;
          border-radius: 8px;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux {
          background: #0f172a;
          border: 1px solid #334155;
          box-shadow: 0 24px 80px rgba(2, 6, 23, 0.75);
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-header,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-footer {
          background: #0f172a;
          color: #e2e8f0;
          border-color: #334155;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-header h3,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content h4,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content h5,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content p,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content label,
        .swagger-dark-override .swagger-ui .auth-container h4,
        .swagger-dark-override .swagger-ui .auth-container h5,
        .swagger-dark-override .swagger-ui .auth-container p,
        .swagger-dark-override .swagger-ui .auth-container label,
        .swagger-dark-override .swagger-ui .scope-def {
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content {
          border-top: 1px solid #1e293b;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-footer {
          border-top: 1px solid #1e293b;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-header .close-modal {
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content input[type="text"],
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content input[type="password"] {
          background: #111827;
          border: 1px solid #334155;
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content input[type="text"]:focus,
        .swagger-dark-override .swagger-ui .dialog-ux .modal-ux-content input[type="password"]:focus {
          border-color: #60a5fa;
          box-shadow: 0 0 0 1px #60a5fa;
          outline: none;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .auth-btn-wrapper .btn-done {
          background: #111827;
          border-color: #475569;
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .auth-btn-wrapper .authorize {
          background: #22c55e;
          border-color: #22c55e;
          color: #0a0e17;
        }
        .swagger-dark-override .swagger-ui .dialog-ux .auth-btn-wrapper .authorize:hover {
          background: #16a34a;
          border-color: #16a34a;
        }
        .swagger-dark-override .swagger-ui .auth-container .scope-def,
        .swagger-dark-override .swagger-ui .auth-container .scopes h2,
        .swagger-dark-override .swagger-ui .auth-container .scope-contents,
        .swagger-dark-override .swagger-ui .auth-container .errors {
          color: #cbd5e1;
        }
        .swagger-dark-override .swagger-ui .auth-container input[type="checkbox"] {
          accent-color: #22c55e;
        }
        .swagger-dark-override .swagger-ui .dialog-ux {
          background: rgba(2, 6, 23, 0.7);
        }
        .swagger-dark-override .swagger-ui .info .description code {
          color: #4ade80;
          background: #1a2332;
          padding: 2px 6px;
          border-radius: 4px;
        }
        .swagger-dark-override .swagger-ui .filter .operation-filter-input {
          background: #0a0e17;
          border-color: #334155;
          color: #e2e8f0;
        }
        .swagger-dark-override .swagger-ui .response-col_status {
          color: #e2e8f0;
        }
      `}</style>
    </div>
  );
}
