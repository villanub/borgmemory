"use client";

import { useEffect } from "react";

export default function OAuth2Redirect() {
  useEffect(() => {
    // Load the Swagger UI oauth2-redirect script which handles the redirect flow
    const script = document.createElement("script");
    script.src = "/swagger-ui/oauth2-redirect.js";
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return null;
}
