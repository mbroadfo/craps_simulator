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
const ECS_UPDATE = "AmazonEC2ContainerServiceV20141113.UpdateService";
const ECS_DESCRIBE = "AmazonEC2ContainerServiceV20141113.DescribeServices";

// Path the warming page polls. Served by this Worker, NOT the origin: a poll
// to /health cannot work, because Access answers it long before the origin
// would (see serviceIsRunning).
const STATUS_PATH = "/__waker/status";

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
async function signedEcsRequest(env, body, target) {
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
    `x-amz-target:${target}\n`;
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
      "X-Amz-Target": target,
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
  const res = await fetch(await signedEcsRequest(env, body, ECS_UPDATE));
  if (!res.ok) {
    console.log("wake failed", res.status, await res.text());
  }
  return res.ok;
}

// Cached briefly so a burst of requests (page + assets) costs one API call.
let runningCache = { at: 0, running: false };

/**
 * Whether the service currently has a task.
 *
 * Asks ECS rather than probing the origin over HTTP. An earlier version
 * fetched /health through the public hostname, but Access sits in front of
 * the origin and answers with a 302 to its login page -- and fetch() follows
 * redirects by default, so the probe landed on a login page returning 200 and
 * concluded the origin was healthy. The wake therefore never fired and every
 * visit ended at Cloudflare error 1033.
 */
async function serviceIsRunning(env) {
  const now = Date.now();
  if (now - runningCache.at < 10000) return runningCache.running;

  let running = false;
  try {
    const body = JSON.stringify({ cluster: env.ECS_CLUSTER, services: [env.ECS_SERVICE] });
    const res = await fetch(await signedEcsRequest(env, body, ECS_DESCRIBE));
    if (res.ok) {
      const data = await res.json();
      const svc = (data.services || [])[0] || {};
      running = (svc.runningCount || 0) >= 1;
    } else {
      console.log("describe failed", res.status, (await res.text()).slice(0, 200));
    }
  } catch (err) {
    console.log("describe threw", String(err));
  }

  runningCache = { at: now, running };
  return running;
}

/**
 * Whether this request should be allowed to start a Fargate task.
 *
 * IMPORTANT: this Worker runs BEFORE Cloudflare Access, so it cannot know
 * whether the visitor is authenticated. Verified empirically -- an
 * unauthenticated request reaches this Worker and only becomes a 302 when
 * the Worker passes it through to the origin, which is where Access sits.
 * An earlier version required a CF_Authorization cookie; that cookie does
 * not exist on a first visit (Access sets it only after login), so the wake
 * never fired and the visitor got Cloudflare error 1033 instead.
 *
 * So the wake cannot be gated on identity. It is gated on the request
 * looking like a real browser navigation instead, which keeps scanners and
 * asset probes from starting the task. The residual risk is bounded and
 * small: someone who knows the URL can cause a wake, but Access still stops
 * them using the app, and the container sleeps itself again after
 * CRAPS_IDLE_SHUTDOWN_MINUTES. Worst case is a container that stays warm,
 * not an open service.
 */
function looksLikeNavigation(request) {
  if (request.method !== "GET") return false;
  const accept = request.headers.get("Accept") || "";
  return accept.includes("text/html");
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
      const r = await fetch('/__waker/status', { cache: 'no-store' });
      const d = await r.json();
      // A task exists, but cloudflared still has to register with the edge
      // (~15s after the container starts). Reloading the instant the task
      // appears just shows error 1033 instead.
      if (d.running) { setTimeout(() => location.reload(), 15000); return; }
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

// Exported for out-of-runtime testing (scripts/verify_waker_sigv4.mjs).
// The SigV4 implementation is the one piece that cannot be exercised through
// the deployed Worker, because Access blocks unauthenticated access to it.
export { signedEcsRequest, ECS_DESCRIBE, ECS_UPDATE };

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const running = await serviceIsRunning(env);

    // Polled by the warming page. Answered here because anything served by
    // the origin is behind Access and unreachable while the task is down.
    if (url.pathname === STATUS_PATH) {
      return new Response(JSON.stringify({ running }), {
        headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
      });
    }

    if (running) {
      return fetch(request);
    }

    const wakeable = looksLikeNavigation(request);
    console.log(JSON.stringify({
      at: "waker", path: url.pathname, running, wakeable, method: request.method,
    }));

    // Not a browser navigation (asset probe, scanner, HEAD/POST): fall
    // through rather than starting a task.
    if (!wakeable) {
      return fetch(request);
    }

    ctx.waitUntil(wakeService(env));
    return warmingPage(15);
  },
};
