import { randomBytes } from "node:crypto";
import { config as waspConfig } from "wasp/server";
import type { MiddlewareConfigFn } from "wasp/server";
import type { PaymentsWebhook } from "wasp/server/api";
import type {
  CreateCheckoutSessionArgs,
  FetchCustomerPortalUrlArgs,
  PaymentProcessor,
} from "../paymentProcessor";
import { PaymentPlanId } from "../plans";
import { getZpayConfig } from "./config";

const ZPAY_PROVIDER = "zpay";
const PENDING_ORDER_STATUS = "pending";

const zpayMiddlewareConfigFn: MiddlewareConfigFn = (middlewareConfig) =>
  middlewareConfig;

const unsupportedZpayGenericWebhook: PaymentsWebhook = async (
  _request,
  response,
) =>
  response.status(404).json({
    error: "ZPAY webhook uses /payments/zpay/notify.",
  });

export const zpayPaymentProcessor: PaymentProcessor = {
  id: ZPAY_PROVIDER,
  createCheckoutSession: async ({
    paymentPlan,
    paymentPlanId,
    prismaPaymentOrderDelegate,
    userId,
  }: CreateCheckoutSessionArgs) => {
    if (
      paymentPlanId !== PaymentPlanId.Credits10 ||
      paymentPlan.effect.kind !== "credits"
    ) {
      throw new Error(
        "ZPAY currently supports one-time Credits10 purchases only.",
      );
    }

    const zpayConfig = getZpayConfig();
    const order = await prismaPaymentOrderDelegate.create({
      data: {
        amountCents: zpayConfig.credits10AmountCents,
        checkoutToken: randomToken(24),
        currency: "CNY",
        outTradeNo: createOutTradeNo(),
        planId: paymentPlanId,
        provider: ZPAY_PROVIDER,
        status: PENDING_ORDER_STATUS,
        userId,
      },
      select: {
        checkoutToken: true,
        outTradeNo: true,
      },
    });

    const checkoutUrl = new URL(
      `${waspConfig.serverUrl}/payments/zpay/checkout`,
    );
    checkoutUrl.searchParams.set("out_trade_no", order.outTradeNo);
    checkoutUrl.searchParams.set("token", order.checkoutToken);

    return {
      session: {
        id: order.outTradeNo,
        url: checkoutUrl.toString(),
      },
    };
  },
  fetchCustomerPortalUrl: async (_args: FetchCustomerPortalUrlArgs) => null,
  webhook: unsupportedZpayGenericWebhook,
  webhookMiddlewareConfigFn: zpayMiddlewareConfigFn,
};

function createOutTradeNo(): string {
  return `ct${Date.now()}${randomBytes(5).toString("hex")}`;
}

function randomToken(byteLength: number): string {
  return randomBytes(byteLength).toString("hex");
}
