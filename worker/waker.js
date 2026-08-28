/**
 * Wakes the Fargate service on demand, so it can sleep the rest of the time.
 *
 * The service idles at desiredCount 0 (see terraform/ecs.tf) and the app
 * scales itself back down when nobody is using it. Something has to start it
 * again, and AWS has no "HTTP request arrives -> start the task" primitive.
 * This Worker is that missing piece: it sits on the hostname's route, notices
 * the origin is down, asks ECS for one task, and holds the visitor on a
 * self-refreshing page until the container answers.
 *
 * Deliberately dependency-free: SigV4 is implemented below against Web Crypto
 * so the whole thing is one file Terraform can upload, with no bundler.
 */

const AWS_SERVICE = "ecs";
const ECS_TARGET = "AmazonEC2ContainerServiceV20141113.UpdateService";

// Short: this runs on every request while the origin is down, and a visitor
// is waiting on it.
const HEALTH_TIMEOUT_MS = 3000;

const enc = new TextEncoder();

async function sha256Hex(data) {
  const buf = await crypto.subtle.digest("SHA-256", typeof data === "string" ? enc.encode(data) : data);
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function hmac(key, data) {
  const k = await crypto.subtle.importKey("raw", typeof key === "string" ? enc.encode(key) : key,
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(data)));
}

/** Minimal SigV4 for a single known POST. Not a general AWS client. */
async function signedEcsRequest(env, body) {
  const region = env.AWS_REGION;
  const host = `${AWS_SERVICE}.${region}.amazonaws.com`;
  const now = new Date();
  const amzDate = now.toISOString().replace(/[:-]|\.\d{3}/g, "");
  const dateStamp = amzDate.slice(0, 8);

  const payloadHash = await sha256Hex(body);
  const canonicalHeaders =
    `content-type:application/x-amz-json-1.1\n` +
    `host:${host}\n` +
    `x-amz-date:${amzDate}\n` +
    `x-amz-target:${ECS_TARGET}\n`;
  const signedHeaders = "content-type;host;x-amz-date;x-amz-target";
  const canonicalRequest = ["POST", "/", "", canonicalHeaders, signedHeaders, payloadHash].join("\n");

  const scope = `${dateStamp}/${region}/${AWS_SERVICE}/aws4_request`;
  const stringToSign = ["AWS4-HMAC-SHA256", amzDate, scope, await sha256Hex(canonicalRequest)].join("\n");

  let key = await hmac(`AWS4${env.AWS_SECRET_ACCESS_KEY}`, dateStamp);
  key = await hmac(key, region);
  key = await hmac(key, AWS_SERVICE);
  key = await hmac(key, "aws4_request");
  const sigBytes = await hmac(key, stringToSign);
  const signature = [...sigBytes].map((b) => b.toString(16).padStart(2, "0")).join("");

  return new Request(`https://${host}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": ECS_TARGET,
      "X-Amz-Date": amzDate,
      Authorization:
        `AWS4-HMAC-SHA256 Credential=${env.AWS_ACCESS_KEY_ID}/${scope}, ` +
        `SignedHeaders=${signedHeaders}, Signature=${signature}`,
    },
    body,
  });
}

async function wakeService(env) {
  const body = JSON.stringify({
    cluster: env.ECS_CLUSTER,
    service: env.ECS_SERVICE,
    desiredCount: 1,
  });
  const res = await fetch(await signedEcsRequest(env, body));
  if (!res.ok) {
    console.log("wake failed", res.status, await res.text());
  }
  return res.ok;
}

async function originIsUp(url) {
  try {
    const res = await fetch(new URL("/health", url).toString(), {
      method: "GET",
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Access sets this once a visitor has authenticated. Checking it means an
 * unauthenticated request can never start a Fargate task -- which is the
 * whole point of putting Access in front: the cost risk is someone finding
 * the URL and keeping the container awake.
 */
function isAuthenticated(request) {
  if (request.headers.get("Cf-Access-Jwt-Assertion")) return true;
  const cookie = request.headers.get("Cookie") || "";
  return /(?:^|;\s*)CF_Authorization=/.test(cookie);
}

function warmingPage(retryAfterSeconds) {
  return new Response(
    `<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Starting up...</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; min-height:100vh; display:grid; place-items:center;
         background:#04060a; color:#c9a84c;
         font-family: "Barlow Condensed", system-ui, sans-serif; }
  .box { text-align:center; padding:2rem; }
  h1 { font-size:1.6rem; letter-spacing:.14em; text-transform:uppercase; margin:0 0 .6rem; }
  p { color:#8a8171; margin:.3rem 0; font-size:.95rem; }
  .dice { font-size:3rem; margin-bottom:1rem; animation:roll 1.2s ease-in-out infinite; }
  @keyframes roll { 0%,100%{transform:rotate(-12deg)} 50%{transform:rotate(12deg)} }
  @media (prefers-reduced-motion: reduce) { .dice { animation: none } }
</style>
<div class="box">
  <div class="dice">&#127922;</div>
  <h1>Warming up the table</h1>
  <p>The server sleeps when idle to keep it cheap.</p>
  <p>This takes about a minute &mdash; the page will reload itself.</p>
</div>
<script>
  const started = Date.now();
  async function poll() {
    try {
      const r = await fetch('/health', { cache: 'no-store' });
      if (r.ok) { location.reload(); return; }
    } catch (e) { /* still down */ }
    if (Date.now() - started < 240000) setTimeout(poll, 3000);
  }
  setTimeout(poll, 5000);
</script>`,
    {
      status: 503,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store",
        "Retry-After": String(retryAfterSeconds),
      },
    },
  );
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (await originIsUp(url)) {
      return fetch(request);
    }

    // Origin is down. Only an authenticated visitor may start it; anyone
    // else falls through to Access (or Cloudflare's own 1033).
    if (!isAuthenticated(request)) {
      return fetch(request);
    }

    // The visitor should not wait on the AWS API call itself.
    ctx.waitUntil(wakeService(env));
    return warmingPage(15);
  },
};
