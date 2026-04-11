const fs = require("fs");
const OpenTimestamps = require("opentimestamps");

function fileExists(p) {
  try {
    return !!p && fs.existsSync(p);
  } catch {
    return false;
  }
}

function readFileBuffer(p) {
  return fs.readFileSync(p);
}

function toPosix(p) {
  return String(p || "").replace(/\\/g, "/");
}

function envRequired(name) {
  const v = process.env[name];
  if (!v) {
    throw new Error(`Missing required env: ${name}`);
  }
  return v;
}

function envOptional(name) {
  return process.env[name] || "";
}

function buildArtifact(baseUrl, p) {
  if (!p) {
    return {
      path: null,
      exists: false,
      url: null
    };
  }
  return {
    path: p,
    exists: fileExists(p),
    url: `${baseUrl}/${toPosix(p)}`
  };
}

function parseInfoForPending(infoText) {
  const lines = infoText.split(/\r?\n/);
  const pendingCalendars = [];
  const blockAttestations = [];

  for (const line of lines) {
    const pendingMatch = line.match(/PendingAttestation\('([^']+)'\)/);
    if (pendingMatch) pendingCalendars.push(pendingMatch[1]);

    const blockMatch = line.match(/BitcoinBlockHeaderAttestation\((\d+)\)/);
    if (blockMatch) blockAttestations.push(Number(blockMatch[1]));
  }

  return { pendingCalendars, blockAttestations };
}

async function main() {
  const repo = envRequired("REPO_NAME");
  const owner = envRequired("REPO_OWNER");
  const manifestPath = envRequired("MANIFEST_PATH");
  const otsPath = envRequired("OTS_PATH");
  const receiptPath = envRequired("RECEIPT_PATH");
  const bundlePath = envOptional("BUNDLE_PATH");

  const baseUrl = `https://${owner}.github.io/${repo}`;

  const status = {
    stage: "Stage266",
    title: "Verified Public Evidence",
    generated_at: new Date().toISOString(),
    verification_url: `${baseUrl}/`,
    artifacts: {
      manifest: buildArtifact(baseUrl, manifestPath),
      ots_proof: buildArtifact(baseUrl, otsPath),
      receipt: buildArtifact(baseUrl, receiptPath),
      bundle: buildArtifact(baseUrl, bundlePath)
    },
    ots: {
      status: "error",
      verified: false,
      block_height: null,
      timestamp_unix: null,
      timestamp_iso: null,
      pending_calendars: [],
      bitcoin_block_attestations: [],
      notes: []
    },
    final_status: "error"
  };

  if (!status.artifacts.manifest.exists) {
    status.ots.notes.push("Manifest file not found.");
  }
  if (!status.artifacts.ots_proof.exists) {
    status.ots.notes.push("OTS proof file not found.");
  }
  if (!status.artifacts.receipt.exists) {
    status.ots.notes.push("Receipt file not found.");
  }
  if (!bundlePath) {
    status.ots.notes.push("Bundle path is not configured for this stage.");
  } else if (!status.artifacts.bundle.exists) {
    status.ots.notes.push("Bundle file path is configured, but the file does not exist.");
  }

  if (!status.artifacts.manifest.exists || !status.artifacts.ots_proof.exists) {
    fs.writeFileSync(
      "docs/status/verification_status.json",
      JSON.stringify(status, null, 2) + "\n",
      "utf8"
    );
    return;
  }

  try {
    const fileBytes = readFileBuffer(manifestPath);
    const otsBytes = readFileBuffer(otsPath);

    const detached = OpenTimestamps.DetachedTimestampFile.fromBytes(
      new OpenTimestamps.Ops.OpSHA256(),
      fileBytes
    );
    const detachedOts = OpenTimestamps.DetachedTimestampFile.deserialize(otsBytes);

    const infoText = OpenTimestamps.info(detachedOts);
    const parsed = parseInfoForPending(infoText);

    status.ots.pending_calendars = parsed.pendingCalendars;
    status.ots.bitcoin_block_attestations = parsed.blockAttestations;

    let verifyResult;
    try {
      verifyResult = await OpenTimestamps.verify(detachedOts, detached, {
        ignoreBitcoinNode: true,
        timeout: 5000
      });
    } catch (verifyErr) {
      status.ots.notes.push(`verify exception: ${String(verifyErr.message || verifyErr)}`);
    }

    if (verifyResult && verifyResult.bitcoin) {
      status.ots.status = "confirmed";
      status.ots.verified = true;
      status.ots.block_height = verifyResult.bitcoin.height ?? null;
      status.ots.timestamp_unix = verifyResult.bitcoin.timestamp ?? null;
      status.ots.timestamp_iso = verifyResult.bitcoin.timestamp
        ? new Date(verifyResult.bitcoin.timestamp * 1000).toISOString()
        : null;
      status.final_status = "confirmed";
    } else if (status.ots.pending_calendars.length > 0) {
      status.ots.status = "pending";
      status.ots.verified = false;
      status.final_status = "pending";
    } else if (status.ots.bitcoin_block_attestations.length > 0) {
      status.ots.status = "attested_but_not_fully_verified";
      status.ots.verified = false;
      status.final_status = "warning";
      status.ots.notes.push("Bitcoin block attestation is present in proof, but verify did not return a confirmed result.");
    } else {
      status.ots.status = "unknown";
      status.ots.verified = false;
      status.final_status = "warning";
      status.ots.notes.push("OTS proof exists but no pending or confirmed status could be determined.");
    }
  } catch (err) {
    status.ots.status = "error";
    status.ots.verified = false;
    status.final_status = "error";
    status.ots.notes.push(`fatal exception: ${String(err.message || err)}`);
  }

  fs.writeFileSync(
    "docs/status/verification_status.json",
    JSON.stringify(status, null, 2) + "\n",
    "utf8"
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
