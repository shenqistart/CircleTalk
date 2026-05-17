import type { User } from "wasp/entities";
import { HttpError } from "wasp/server";
import { SubscriptionStatus } from "./plans";

export function isUserSubscribed(user: Pick<User, "subscriptionStatus">) {
  return user.subscriptionStatus === SubscriptionStatus.Active;
}

export function getRoundtableCreditDebitAmount(
  user: Pick<User, "subscriptionStatus">,
  requestedCredits: number,
) {
  return isUserSubscribed(user) ? 0 : requestedCredits;
}

export function assertCanReserveRoundtableUsage(
  user: Pick<User, "credits" | "subscriptionStatus">,
  requestedCredits: number,
  outstandingReservedCredits: number,
) {
  const creditDebitAmount = getRoundtableCreditDebitAmount(
    user,
    requestedCredits,
  );
  if (creditDebitAmount === 0) {
    return creditDebitAmount;
  }
  if (user.credits - outstandingReservedCredits < creditDebitAmount) {
    throw new HttpError(402, "User has no subscription and is out of credits.");
  }
  return creditDebitAmount;
}
