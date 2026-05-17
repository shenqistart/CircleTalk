import type { PrismaClient } from "@prisma/client";
import { type User } from "wasp/entities";
import {
  getSubscriptionPaymentPlanIds,
  SubscriptionStatus,
} from "../../payment/plans";

type MockUserData = Omit<User, "id">;

/**
 * This function, which we've imported in `app.db.seeds` in the `main.wasp` file,
 * seeds the database with mock users via the `wasp db seed` command.
 * For more info see: https://wasp.sh/docs/data-model/backends#seeding-the-database
 */
export async function seedMockUsers(prismaClient: PrismaClient) {
  await Promise.all(
    generateMockUsersData(50).map((data) => prismaClient.user.create({ data })),
  );
}

function generateMockUsersData(numOfUsers: number): MockUserData[] {
  return Array.from({ length: numOfUsers }, (_, index) =>
    generateMockUserData(index),
  );
}

function generateMockUserData(index: number): MockUserData {
  const firstName = pick(FIRST_NAMES);
  const lastName = pick(LAST_NAMES);
  const subscriptionStatus =
    pick<SubscriptionStatus | null>([
      ...Object.values(SubscriptionStatus),
      null,
    ]);
  const now = new Date();
  const createdAt = randomDateBetween(
    new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000),
    now,
  );
  const timePaid = randomDateBetween(createdAt, now);
  const credits = subscriptionStatus ? 0 : randomInt(0, 10);
  const hasUserPaidOnStripe = !!subscriptionStatus || credits > 3;
  return {
    email: `${slugify(firstName)}.${slugify(lastName)}.${index}@example.com`,
    username: `${slugify(firstName)}_${slugify(lastName)}_${index}`,
    createdAt,
    isAdmin: false,
    credits,
    subscriptionStatus,
    lemonSqueezyCustomerPortalUrl: null,
    paymentProcessorUserId: hasUserPaidOnStripe
      ? `cus_test_${randomId()}`
      : null,
    datePaid: hasUserPaidOnStripe
      ? randomDateBetween(createdAt, timePaid)
      : null,
    subscriptionPlan: subscriptionStatus
      ? pick(getSubscriptionPaymentPlanIds())
      : null,
  };
}

function pick<T>(items: T[]): T {
  return items[randomInt(0, items.length - 1)];
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomDateBetween(from: Date, to: Date): Date {
  return new Date(randomInt(from.getTime(), to.getTime()));
}

function randomId(): string {
  return Array.from({ length: 16 }, () => randomInt(0, 15).toString(16)).join(
    "",
  );
}

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

const FIRST_NAMES = [
  "Ada",
  "Grace",
  "Linus",
  "Margaret",
  "Alan",
  "Katherine",
  "Barbara",
  "Donald",
];

const LAST_NAMES = [
  "Lovelace",
  "Hopper",
  "Torvalds",
  "Hamilton",
  "Turing",
  "Johnson",
  "Liskov",
  "Knuth",
];
