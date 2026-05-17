import { createHash, timingSafeEqual } from "node:crypto";

export type ZpaySignableParams = Record<
  string,
  boolean | number | string | null | undefined
>;

const SIGNATURE_KEYS = new Set(["sign", "sign_type"]);

export function canonicalizeZpayParams(params: ZpaySignableParams): string {
  return Object.entries(params)
    .filter(
      ([key, value]) =>
        !SIGNATURE_KEYS.has(key) &&
        value !== undefined &&
        value !== null &&
        String(value) !== "",
    )
    .sort(([leftKey], [rightKey]) => {
      if (leftKey < rightKey) return -1;
      if (leftKey > rightKey) return 1;
      return 0;
    })
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("&");
}

export function signZpayParams(
  params: ZpaySignableParams,
  key: string,
): string {
  return createHash("md5")
    .update(`${canonicalizeZpayParams(params)}${key}`, "utf8")
    .digest("hex")
    .toLowerCase();
}

export function verifyZpaySignature(
  params: ZpaySignableParams,
  key: string,
): boolean {
  const providedSign = params.sign;
  if (
    typeof providedSign !== "string" ||
    !/^[a-f0-9]{32}$/i.test(providedSign)
  ) {
    return false;
  }

  const expectedSign = signZpayParams(params, key);
  return timingSafeEqual(
    Buffer.from(providedSign.toLowerCase(), "utf8"),
    Buffer.from(expectedSign, "utf8"),
  );
}
