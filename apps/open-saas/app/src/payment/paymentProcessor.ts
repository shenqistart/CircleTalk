import { PrismaClient } from "@prisma/client";
import { User } from "wasp/entities";
import type { MiddlewareConfigFn } from "wasp/server";
import type { PaymentsWebhook } from "wasp/server/api";
import type { PaymentPlan, PaymentPlanId } from "./plans";
import { stripePaymentProcessor } from "./stripe/paymentProcessor";
import { zpayPaymentProcessor } from "./zpay/paymentProcessor";

export interface CreateCheckoutSessionArgs {
  userId: User["id"];
  userEmail: NonNullable<User["email"]>;
  paymentPlanId: PaymentPlanId;
  paymentPlan: PaymentPlan;
  prismaUserDelegate: PrismaClient["user"];
  prismaPaymentOrderDelegate: PrismaClient["paymentOrder"];
}

export interface FetchCustomerPortalUrlArgs {
  userId: User["id"];
  prismaUserDelegate: PrismaClient["user"];
}

export interface PaymentProcessor {
  id: "stripe" | "lemonsqueezy" | "polar" | "zpay";
  createCheckoutSession: (
    args: CreateCheckoutSessionArgs,
  ) => Promise<{ session: { id: string; url: string } }>;
  fetchCustomerPortalUrl: (
    args: FetchCustomerPortalUrlArgs,
  ) => Promise<string | null>;
  webhook: PaymentsWebhook;
  webhookMiddlewareConfigFn: MiddlewareConfigFn;
}

export const paymentProcessor: PaymentProcessor =
  getConfiguredPaymentProcessor();
// export const paymentProcessor: PaymentProcessor = lemonSqueezyPaymentProcessor;
// export const paymentProcessor: PaymentProcessor = polarPaymentProcessor;

function getConfiguredPaymentProcessor(): PaymentProcessor {
  const provider = (process.env.PAYMENT_PROVIDER ?? "zpay").toLowerCase();
  switch (provider) {
    case "stripe":
      return stripePaymentProcessor;
    case "zpay":
      return zpayPaymentProcessor;
    default:
      throw new Error(`Unsupported PAYMENT_PROVIDER: ${provider}`);
  }
}
