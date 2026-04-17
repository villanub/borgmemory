"use strict";

function runSwaggerOauthRedirect() {
  const oauth2 = window.opener?.swaggerUIRedirectOauth2;
  if (!oauth2) {
    window.close();
    return;
  }

  const sentState = oauth2.state;
  const redirectUrl = oauth2.redirectUrl;
  let queryParams;

  if (/code|token|error/.test(window.location.hash)) {
    queryParams = window.location.hash.substring(1).replace("?", "&");
  } else {
    queryParams = window.location.search.substring(1);
  }

  const rawPairs = queryParams
    .split("&")
    .filter(Boolean)
    .map((pair) => `"${pair.replace("=", '":"')}"`);

  const parsedParams = rawPairs.length
    ? JSON.parse(`{${rawPairs.join(",")}}`, (key, value) =>
        key === "" ? value : decodeURIComponent(value),
      )
    : {};

  const isValid = parsedParams.state === sentState;
  const flow = oauth2.auth.schema.get("flow");
  const usesAuthorizationCode =
    flow === "accessCode" || flow === "authorizationCode" || flow === "authorization_code";

  if (usesAuthorizationCode && !oauth2.auth.code) {
    if (!isValid) {
      oauth2.errCb({
        authId: oauth2.auth.name,
        source: "auth",
        level: "warning",
        message:
          "Authorization may be unsafe, passed state was changed in server. The passed state wasn't returned from auth server.",
      });
    }

    if (parsedParams.code) {
      delete oauth2.state;
      oauth2.auth.code = parsedParams.code;
      oauth2.callback({ auth: oauth2.auth, redirectUrl });
    } else {
      let oauthErrorMsg;
      if (parsedParams.error) {
        oauthErrorMsg =
          `[${parsedParams.error}]: ` +
          (parsedParams.error_description
            ? `${parsedParams.error_description}. `
            : "no accessCode received from the server. ") +
          (parsedParams.error_uri ? `More info: ${parsedParams.error_uri}` : "");
      }

      oauth2.errCb({
        authId: oauth2.auth.name,
        source: "auth",
        level: "error",
        message:
          oauthErrorMsg || "[Authorization failed]: no accessCode received from the server.",
      });
    }
  } else {
    oauth2.callback({
      auth: oauth2.auth,
      token: parsedParams,
      isValid,
      redirectUrl,
    });
  }

  window.close();
}

if (document.readyState !== "loading") {
  runSwaggerOauthRedirect();
} else {
  document.addEventListener("DOMContentLoaded", runSwaggerOauthRedirect);
}
