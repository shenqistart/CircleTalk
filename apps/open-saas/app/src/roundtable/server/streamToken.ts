import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";
import { HttpError } from "wasp/server";
import { requireNodeEnvVar } from "../../server/utils";

export type RoundtableStreamPurpose = "discussion" | "follow_up";

export type RoundtableStreamTokenClaims = {
  userId: string;
  sessionId: string;
  usageId: string;
  purpose: RoundtableStreamPurpose;
  expiresAt: number;
  nonce: string;
};

const TOKEN_SECRET_ENV = "ROUNDTABLE_STREAM_TOKEN_SECRET";
export const ROUNDTABLE_STREAM_TOKEN_TTL_MS = 5 * 60 * 1000;

export function createStreamTokenNonce() {
  return randomUUID();
}

export function signRoundtableStreamToken(
  claims: RoundtableStreamTokenClaims,
) {
  const payload = Buffer.from(JSON.stringify(claims)).toString("base64url");
  const signature = signPayload(payload);
  return `${payload}.${signature}`;
}

export function verifyRoundtableStreamToken(
  token: string,
): RoundtableStreamTokenClaims {
  const [payload, signature] = token.split(".");
  if (!payload || !signature || !isValidSignature(payload, signature)) {
    throw new HttpError(401, "Invalid Roundtable stream token.");
  }
  let claims: RoundtableStreamTokenClaims;
  try {
    claims = JSON.parse(
      Buffer.from(payload, "base64url").toString("utf8"),
    ) as RoundtableStreamTokenClaims;
  } catch {
    throw new HttpError(401, "Invalid Roundtable stream token claims.");
  }
  if (!claims.userId || !claims.sessionId || !claims.usageId || !claims.nonce) {
    throw new HttpError(401, "Invalid Roundtable stream token claims.");
  }
  if (claims.expiresAt < Date.now()) {
    throw new HttpError(401, "Roundtable stream token expired.");
  }
  return claims;
}

function signPayload(payload: string) {
  return createHmac("sha256", requireNodeEnvVar(TOKEN_SECRET_ENV))
    .update(payload)
    .digest("base64url");
}

function isValidSignature(payload: string, signature: string) {
  const expected = Buffer.from(signPayload(payload));
  const received = Buffer.from(signature);
  return (
    expected.byteLength === received.byteLength &&
    timingSafeEqual(expected, received)
  );
}
