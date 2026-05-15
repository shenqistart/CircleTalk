import { useAuth } from "wasp/client/auth";
import { Link as WaspRouterLink, routes } from "wasp/client/router";
import { Button } from "../client/components/ui/button";

export default function RoundtablePage() {
  const { data: user } = useAuth();

  return (
    <main className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-5xl flex-col gap-8 px-6 py-10 lg:px-8">
      <section className="rounded-lg border border-border bg-card p-8 shadow-sm">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">
              {user?.email}
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal text-foreground">
              Roundtable
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              Your private decision sessions will appear here as the product
              workspace moves into the Wasp shell.
            </p>
          </div>
          <Button asChild>
            <WaspRouterLink to={routes.AccountRoute.to}>Account</WaspRouterLink>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatusMetric label="Credits" value={user?.credits ?? 0} />
        <StatusMetric label="Plan" value={user?.subscriptionStatus ?? "Trial"} />
        <StatusMetric label="Access" value="Google" />
      </section>
    </main>
  );
}

function StatusMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-foreground">{value}</p>
    </div>
  );
}
