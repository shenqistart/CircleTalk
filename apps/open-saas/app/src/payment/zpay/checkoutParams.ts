import { PaymentPlanId } from "../plans";
import { formatCentsAsCny } from "./amount";
import type { ZpayConfig } from "./config";
import { signZpayParams, type ZpaySignableParams } from "./signing";

interface ZpayPaymentOrder {
  amountCents: number;
  outTradeNo: string;
  planId: string;
}

export function buildZpayCheckoutParams(
  order: ZpayPaymentOrder,
  zpayConfig: ZpayConfig,
): ZpaySignableParams {
  if (order.planId !== PaymentPlanId.Credits10) {
    throw new Error(
      "ZPAY only supports Credits10 in the current payment flow.",
    );
  }

  const params: ZpaySignableParams = {
    money: formatCentsAsCny(order.amountCents),
    name: "CircleTalk 10 Credits",
    notify_url: zpayConfig.notifyUrl,
    out_trade_no: order.outTradeNo,
    pid: zpayConfig.pid,
    return_url: zpayConfig.returnUrl,
    type: "alipay",
  };

  return {
    ...params,
    sign: signZpayParams(params, zpayConfig.key),
    sign_type: "MD5",
  };
}
