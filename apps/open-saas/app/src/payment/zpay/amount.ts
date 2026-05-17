const CNY_AMOUNT_PATTERN = /^\d+(?:\.\d{1,2})?$/;

export function parseCnyAmountToCents(amount: string): number {
  const normalized = amount.trim();
  if (!CNY_AMOUNT_PATTERN.test(normalized)) {
    throw new Error(`Invalid CNY amount: ${amount}`);
  }

  const [yuan, fractional = ""] = normalized.split(".");
  return Number(yuan) * 100 + Number(fractional.padEnd(2, "0"));
}

export function formatCentsAsCny(amountCents: number): string {
  if (!Number.isInteger(amountCents) || amountCents < 0) {
    throw new Error(`Invalid cent amount: ${amountCents}`);
  }

  const yuan = Math.floor(amountCents / 100);
  const cents = String(amountCents % 100).padStart(2, "0");
  return `${yuan}.${cents}`;
}
