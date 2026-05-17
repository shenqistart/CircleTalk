import { formatCentsAsCny } from "./amount";
import type { ZpayConfig } from "./config";

export interface ZpayOrderQueryResult {
  money?: string;
  status?: number | string;
  trade_no?: string;
  [key: string]: unknown;
}

export async function fetchZpayOrder(
  zpayConfig: ZpayConfig,
  outTradeNo: string,
): Promise<ZpayOrderQueryResult> {
  const url = new URL(zpayConfig.apiUrl);
  url.searchParams.set("act", "order");
  url.searchParams.set("pid", zpayConfig.pid);
  url.searchParams.set("key", zpayConfig.key);
  url.searchParams.set("out_trade_no", outTradeNo);

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`ZPAY order query failed with HTTP ${response.status}`);
  }

  return (await response.json()) as ZpayOrderQueryResult;
}

export function isConfirmedPaidZpayOrder({
  amountCents,
  orderQuery,
  tradeNo,
}: {
  amountCents: number;
  orderQuery: ZpayOrderQueryResult;
  tradeNo: string;
}): boolean {
  return (
    String(orderQuery.status) === "1" &&
    orderQuery.trade_no === tradeNo &&
    orderQuery.money === formatCentsAsCny(amountCents)
  );
}
