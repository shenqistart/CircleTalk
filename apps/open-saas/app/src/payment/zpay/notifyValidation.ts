import { parseCnyAmountToCents } from "./amount";
import type { ZpayConfig } from "./config";
import { verifyZpaySignature, type ZpaySignableParams } from "./signing";

export interface ZpayNotifyPayload extends ZpaySignableParams {
  money: string;
  out_trade_no: string;
  pid: string;
  trade_no: string;
  trade_status: string;
  type: string;
}

export function normalizeZpayParams(
  query: Record<string, unknown>,
): Record<string, string> {
  return Object.fromEntries(
    Object.entries(query).flatMap(([key, value]) => {
      const normalizedValue = Array.isArray(value) ? value[0] : value;
      if (normalizedValue === undefined || normalizedValue === null) {
        return [];
      }
      return [[key, String(normalizedValue)]];
    }),
  );
}

export function validateZpayNotifyPayload({
  expectedAmountCents,
  params,
  zpayConfig,
}: {
  expectedAmountCents: number;
  params: ZpaySignableParams;
  zpayConfig: ZpayConfig;
}): ZpayNotifyPayload {
  if (!verifyZpaySignature(params, zpayConfig.key)) {
    throw new Error("Invalid ZPAY signature");
  }

  const payload = requireZpayNotifyFields(params);
  if (payload.pid !== zpayConfig.pid) {
    throw new Error("Invalid ZPAY merchant id");
  }
  if (payload.type !== "alipay") {
    throw new Error("Invalid ZPAY payment type");
  }
  if (payload.trade_status !== "TRADE_SUCCESS") {
    throw new Error("ZPAY trade is not successful");
  }
  if (parseCnyAmountToCents(payload.money) !== expectedAmountCents) {
    throw new Error("Invalid ZPAY payment amount");
  }

  return payload;
}

export function buildZpayPaymentEventId(payload: ZpayNotifyPayload): string {
  return `zpay:${payload.out_trade_no}:${payload.trade_no}:TRADE_SUCCESS`;
}

function requireZpayNotifyFields(
  params: ZpaySignableParams,
): ZpayNotifyPayload {
  const payload = params as Partial<ZpayNotifyPayload>;
  const requiredFields = [
    "money",
    "out_trade_no",
    "pid",
    "trade_no",
    "trade_status",
    "type",
  ] as const;

  for (const field of requiredFields) {
    if (typeof payload[field] !== "string" || payload[field] === "") {
      throw new Error(`Missing ZPAY field: ${field}`);
    }
  }

  return payload as ZpayNotifyPayload;
}
