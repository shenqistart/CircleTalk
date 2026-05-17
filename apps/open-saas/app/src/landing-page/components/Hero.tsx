import { Link as WaspRouterLink, routes } from "wasp/client/router";
import { Button } from "../../client/components/ui/button";
import { PRODUCT_DESCRIPTION, PRODUCT_NAME } from "../../shared/common";

export default function Hero() {
  return (
    <div className="relative w-full pt-14">
      <TopGradient />
      <BottomGradient />
      <div className="md:p-24">
        <div className="max-w-8xl mx-auto px-6 lg:px-8">
          <div className="lg:mb-18 mx-auto max-w-3xl text-center">
            <h1 className="text-foreground text-5xl font-bold sm:text-6xl">
              Private AI roundtables for{" "}
              <span className="text-gradient-primary">better decisions</span>
            </h1>
            <p className="text-muted-foreground mx-auto mt-6 max-w-2xl text-lg leading-8">
              {PRODUCT_DESCRIPTION}
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Button size="lg" variant="outline" asChild>
                <WaspRouterLink to={routes.PricingPageRoute.to}>
                  View pricing
                </WaspRouterLink>
              </Button>
              <Button size="lg" variant="default" asChild>
                <WaspRouterLink to={routes.LoginRoute.to}>
                  Start a Circle <span aria-hidden="true">→</span>
                </WaspRouterLink>
              </Button>
            </div>
          </div>
          <div className="mt-14 flow-root sm:mt-14">
            <div
              aria-label={`${PRODUCT_NAME} product preview`}
              className="mx-auto hidden max-w-4xl rounded-xl border bg-card p-4 text-left shadow-2xl ring-1 ring-gray-900/10 md:block"
            >
              <div className="grid gap-3 md:grid-cols-[1fr_14rem]">
                <div className="rounded-lg border bg-background p-5">
                  <p className="text-xs font-medium uppercase text-muted-foreground">
                    Circle prompt
                  </p>
                  <p className="mt-3 text-lg font-semibold">
                    Should we migrate billing and login before the next launch?
                  </p>
                  <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    {["Strategist", "Operator", "Skeptic"].map((persona) => (
                      <div
                        className="rounded-md border bg-muted/40 p-3 text-sm"
                        key={persona}
                      >
                        {persona}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-lg border bg-background p-5">
                  <p className="text-xs font-medium uppercase text-muted-foreground">
                    Usage
                  </p>
                  <p className="mt-3 text-3xl font-bold">1 credit</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Charged when the discussion completes.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TopGradient() {
  return (
    <div
      className="absolute right-0 top-0 -z-10 w-full transform-gpu overflow-hidden blur-3xl sm:top-0"
      aria-hidden="true"
    >
      <div
        className="aspect-1020/880 w-280 flex-none bg-linear-to-tr from-amber-400 to-purple-300 opacity-10 sm:right-1/4 sm:translate-x-1/2 dark:hidden"
        style={{
          clipPath:
            "polygon(80% 20%, 90% 55%, 50% 100%, 70% 30%, 20% 50%, 50% 0)",
        }}
      />
    </div>
  );
}

function BottomGradient() {
  return (
    <div
      className="absolute inset-x-0 top-[calc(100%-40rem)] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[calc(100%-65rem)]"
      aria-hidden="true"
    >
      <div
        className="relative aspect-1020/880 w-360 bg-linear-to-br from-amber-400 to-purple-300 opacity-10 sm:-left-3/4 sm:translate-x-1/4 dark:hidden"
        style={{
          clipPath: "ellipse(80% 30% at 80% 50%)",
        }}
      />
    </div>
  );
}
