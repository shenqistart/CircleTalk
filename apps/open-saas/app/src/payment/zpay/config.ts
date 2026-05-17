import { config as waspConfig } from "wasp/server";
import { requireNodeEnvVar } from "../../server/utils";
import { parseCnyAmountToCents } from "./amount";

export interface ZpayConfig {
  pid: string;
  key: string;
  submitUrl: string;
  apiUrl: string;
  notifyUrl: string;
  returnUrl: string;
  credits10AmountCents: number;
}

export function getZpayConfig(): ZpayConfig {
  return {
    pid: requireNodeEnvVar("ZPAY_PID"),
    key: requireNodeEnvVar("ZPAY_KEY"),
    submitUrl: process.env.ZPAY_SUBMIT_URL ?? "https://zpayz.cn/submit.php",
    apiUrl: process.env.ZPAY_API_URL ?? "https://zpayz.cn/api.php",
    notifyUrl:
      process.env.ZPAY_NOTIFY_URL ??
      `${waspConfig.serverUrl}/payments/zpay/notify`,
    returnUrl:
      process.env.ZPAY_RETURN_URL ?? `${waspConfig.frontendUrl}/checkout`,
    credits10AmountCents: parseCnyAmountToCents(
      process.env.PAYMENTS_CREDITS_10_AMOUNT_CNY ?? "9.90",
    ),
  };
}
