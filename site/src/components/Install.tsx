"use client";

import { useState } from "react";

const FULL =
  "curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh\nborg init";

export function Install() {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(FULL);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="install" id="install">
      <div className="cmd">
        <div>
          <span className="p">$</span>curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh
        </div>
        <div>
          <span className="p">$</span>borg init
        </div>
      </div>
      <div
        className="copy"
        onClick={copy}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && copy()}
      >
        {copied ? "copied" : "copy"}
      </div>
    </div>
  );
}
