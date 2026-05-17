import { describe, expect, test } from "vitest";
import {
  formatCentsAsCny,
  parseCnyAmountToCents,
} from "../../src/payment/zpay/amount.ts";
import { renderZpayCheckoutHtml } from "../../src/payment/zpay/checkoutHtml.ts";
import {
  buildZpayPaymentEventId,
  validateZpayNotifyPayload,
} from "../../src/payment/zpay/notifyValidation.ts";
import {
  canonicalizeZpayParams,
  signZpayParams,
  verifyZpaySignature,
} from "../../src/payment/zpay/signing.ts";

const zpayConfig = {
  apiUrl: "https://zpayz.cn/api.php",
  credits10AmountCents: 990,
  key: "merchant_secret",
  notifyUrl: "https://example.com/payments/zpay/notify",
  pid: "1001",
  returnUrl: "https://example.com/checkout",
  submitUrl: "https://zpayz.cn/submit.php",
};

describe("ZPAY payment helpers", () => {
  test("ZPAY signing excludes empty, sign, and sign_type fields", () => {
    const params = {
      empty: "",
      money: "9.90",
      out_trade_no: "ct_test",
      pid: "1001",
      sign: "ignored",
      sign_type: "MD5",
      type: "alipay",
    };

    expect(canonicalizeZpayParams(params)).toBe(
      "money=9.90&out_trade_no=ct_test&pid=1001&type=alipay",
    );
    expect(signZpayParams(params, zpayConfig.key)).toBe(
      signZpayParams(
        {
          money: "9.90",
          out_trade_no: "ct_test",
          pid: "1001",
          type: "alipay",
        },
        zpayConfig.key,
      ),
    );
  });

  test("ZPAY signature verification rejects tampered amounts", () => {
    const signedParams = {
      money: "9.90",
      out_trade_no: "ct_test",
      pid: "1001",
      type: "alipay",
    };
    const sign = signZpayParams(signedParams, zpayConfig.key);

    expect(verifyZpaySignature({ ...signedParams, sign }, zpayConfig.key)).toBe(
      true,
    );
    expect(
      verifyZpaySignature(
        { ...signedParams, money: "0.01", sign },
        zpayConfig.key,
      ),
    ).toBe(false);
  });

  test("ZPAY notify validation accepts only matching successful Alipay notifications", () => {
    const params = {
      money: "9.90",
      out_trade_no: "ct_test",
      pid: "1001",
      trade_no: "zpay_trade_1",
      trade_status: "TRADE_SUCCESS",
      type: "alipay",
    };
    const sign = signZpayParams(params, zpayConfig.key);
    const payload = validateZpayNotifyPayload({
      expectedAmountCents: 990,
      params: { ...params, sign, sign_type: "MD5" },
      zpayConfig,
    });

    expect(payload.trade_no).toBe("zpay_trade_1");
    expect(buildZpayPaymentEventId(payload)).toBe(
      "zpay:ct_test:zpay_trade_1:TRADE_SUCCESS",
    );
  });

  test("ZPAY notify validation rejects wrong merchant, amount, and status", () => {
    const baseParams = {
      money: "9.90",
      out_trade_no: "ct_test",
      pid: "1001",
      trade_no: "zpay_trade_1",
      trade_status: "TRADE_SUCCESS",
      type: "alipay",
    };
    expect(() =>
      validateZpayNotifyPayload({
        expectedAmountCents: 990,
        params: signTestPayload({ ...baseParams, pid: "9999" }),
        zpayConfig,
      }),
    ).toThrow();
    expect(() =>
      validateZpayNotifyPayload({
        expectedAmountCents: 990,
        params: signTestPayload({ ...baseParams, money: "19.90" }),
        zpayConfig,
      }),
    ).toThrow();
    expect(() =>
      validateZpayNotifyPayload({
        expectedAmountCents: 990,
        params: signTestPayload({
          ...baseParams,
          trade_status: "WAIT_BUYER_PAY",
        }),
        zpayConfig,
      }),
    ).toThrow();
  });

  test("CNY amount helpers use exact cents", () => {
    expect(parseCnyAmountToCents("9.90")).toBe(990);
    expect(parseCnyAmountToCents("9.9")).toBe(990);
    expect(formatCentsAsCny(990)).toBe("9.90");
    expect(() => parseCnyAmountToCents("9.999")).toThrow();
  });

  test("ZPAY checkout HTML does not expose the merchant key", () => {
    const html = renderZpayCheckoutHtml({
      params: {
        money: "9.90",
        out_trade_no: "ct_test",
        pid: "1001",
        sign: "signature",
        sign_type: "MD5",
        type: "alipay",
      },
      submitUrl: zpayConfig.submitUrl,
    });

    expect(html).toMatch(/method="post"/);
    expect(html).toMatch(/name="sign"/);
    expect(html).not.toMatch(/merchant_secret/);
  });
});

function signTestPayload(params: Record<string, string>) {
  return {
    ...params,
    sign: signZpayParams(params, zpayConfig.key),
    sign_type: "MD5",
  };
}
