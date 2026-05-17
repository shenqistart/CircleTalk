import { Prisma } from "@prisma/client";
import { prisma } from "wasp/server";
import type { ZpayCheckout, ZpayPaymentNotify } from "wasp/server/api";
import { buildZpayCheckoutParams } from "./checkoutParams";
import { renderZpayCheckoutHtml } from "./checkoutHtml";
import { getZpayConfig } from "./config";
import { fetchZpayOrder, isConfirmedPaidZpayOrder } from "./orderQuery";
import {
  buildZpayPaymentEventId,
  normalizeZpayParams,
  validateZpayNotifyPayload,
} from "./notifyValidation";

const ZPAY_PROVIDER = "zpay";
const PAID_ORDER_STATUS = "paid";
const PENDING_ORDER_STATUS = "pending";
const CREDITS_10_AMOUNT = 10;

export const zpayCheckout: ZpayCheckout = async (request, response) => {
  const outTradeNo = getQueryParam(request.query.out_trade_no);
  const checkoutToken = getQueryParam(request.query.token);
  if (!outTradeNo || !checkoutToken) {
    return response.status(404).send("Not found");
  }

  const order = await prisma.paymentOrder.findFirst({
    where: {
      checkoutToken,
      outTradeNo,
      provider: ZPAY_PROVIDER,
    },
    select: {
      amountCents: true,
      outTradeNo: true,
      planId: true,
      status: true,
    },
  });

  if (!order) {
    return response.status(404).send("Not found");
  }

  const zpayConfig = getZpayConfig();
  if (order.status === PAID_ORDER_STATUS) {
    return response.redirect(
      buildCheckoutReturnUrl(zpayConfig.returnUrl, order.outTradeNo, "success"),
    );
  }

  const checkoutParams = buildZpayCheckoutParams(order, zpayConfig);
  response.setHeader("Content-Type", "text/html; charset=utf-8");
  response.setHeader("Cache-Control", "no-store");
  return response.status(200).send(
    renderZpayCheckoutHtml({
      params: checkoutParams,
      submitUrl: zpayConfig.submitUrl,
    }),
  );
};

export const zpayPaymentNotify: ZpayPaymentNotify = async (
  request,
  response,
) => {
  try {
    const zpayConfig = getZpayConfig();
    const params = normalizeZpayParams(request.query);
    const outTradeNo = getQueryParam(params.out_trade_no);
    if (!outTradeNo) {
      return sendZpayFail(response, "Missing out_trade_no");
    }

    const order = await prisma.paymentOrder.findUnique({
      where: { outTradeNo },
      select: {
        amountCents: true,
        id: true,
        outTradeNo: true,
        planId: true,
        provider: true,
        status: true,
        userId: true,
      },
    });
    if (!order || order.provider !== ZPAY_PROVIDER) {
      return sendZpayFail(response, "Unknown order");
    }

    const payload = validateZpayNotifyPayload({
      expectedAmountCents: order.amountCents,
      params,
      zpayConfig,
    });
    const remoteOrder = await fetchZpayOrder(zpayConfig, order.outTradeNo);
    if (
      !isConfirmedPaidZpayOrder({
        amountCents: order.amountCents,
        orderQuery: remoteOrder,
        tradeNo: payload.trade_no,
      })
    ) {
      return sendZpayFail(response, "ZPAY order query did not confirm payment");
    }

    const eventId = buildZpayPaymentEventId(payload);
    await prisma.$transaction(async (tx) => {
      await tx.paymentWebhookEvent.create({
        data: {
          eventId,
          eventType: payload.trade_status,
          metadataJson: toPrismaJson({
            notify: params,
            remoteOrder,
          }),
          provider: ZPAY_PROVIDER,
          userId: order.userId,
        },
      });

      const updateResult = await tx.paymentOrder.updateMany({
        data: {
          paidAt: new Date(),
          providerTradeNo: payload.trade_no,
          rawNotifyJson: toPrismaJson(params),
          status: PAID_ORDER_STATUS,
        },
        where: {
          id: order.id,
          status: PENDING_ORDER_STATUS,
        },
      });

      if (updateResult.count === 1) {
        await tx.user.update({
          data: {
            credits: { increment: CREDITS_10_AMOUNT },
            datePaid: new Date(),
          },
          where: { id: order.userId },
        });
      }
    });

    return sendZpaySuccess(response);
  } catch (error) {
    if (isUniqueConstraintError(error)) {
      return sendZpaySuccess(response);
    }
    console.error("ZPAY payment notify error:", getSafeErrorMessage(error));
    return sendZpayFail(response, getSafeErrorMessage(error));
  }
};

function buildCheckoutReturnUrl(
  baseReturnUrl: string,
  outTradeNo: string,
  status: "success",
): string {
  const url = new URL(baseReturnUrl);
  url.searchParams.set("provider", "zpay");
  url.searchParams.set("out_trade_no", outTradeNo);
  url.searchParams.set("status", status);
  return url.toString();
}

function getQueryParam(value: unknown): string | undefined {
  const normalizedValue = Array.isArray(value) ? value[0] : value;
  return typeof normalizedValue === "string" && normalizedValue !== ""
    ? normalizedValue
    : undefined;
}

function isUniqueConstraintError(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    error.code === "P2002"
  );
}

function sendZpaySuccess(response: Parameters<ZpayPaymentNotify>[1]) {
  return response.status(200).send("success");
}

function sendZpayFail(
  response: Parameters<ZpayPaymentNotify>[1],
  message: string,
) {
  return response.status(400).send(`fail:${message}`);
}

function getSafeErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unknown ZPAY error";
}

function toPrismaJson(value: unknown): Prisma.InputJsonValue {
  return JSON.parse(JSON.stringify(value)) as Prisma.InputJsonValue;
}
