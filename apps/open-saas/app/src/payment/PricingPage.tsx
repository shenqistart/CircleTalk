import { CheckCircle } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "wasp/client/auth";
import { generateCheckoutSession } from "wasp/client/operations";
import { Alert, AlertDescription } from "../client/components/ui/alert";
import { Button } from "../client/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardTitle,
} from "../client/components/ui/card";
import { PaymentPlanId, prettyPaymentPlanName } from "./plans";

const credits10PriceLabel =
  import.meta.env.REACT_APP_CREDITS_10_PRICE_LABEL ?? "¥9.90";

const creditsPlan = {
  description: "One-time Alipay purchase for additional Circle discussions.",
  features: [
    "10 discussion credits",
    "Alipay payment",
    "Credits are added after payment notification",
  ],
  name: prettyPaymentPlanName(PaymentPlanId.Credits10),
  price: credits10PriceLabel,
};

const PricingPage = () => {
  const [isPaymentLoading, setIsPaymentLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { data: user } = useAuth();
  const navigate = useNavigate();

  async function handleBuyNowClick() {
    if (!user) {
      navigate("/login");
      return;
    }
    try {
      setIsPaymentLoading(true);
      const checkoutResults = await generateCheckoutSession(
        PaymentPlanId.Credits10,
      );

      if (checkoutResults?.sessionUrl) {
        window.open(checkoutResults.sessionUrl, "_self");
      } else {
        throw new Error("Error generating checkout session URL");
      }
    } catch (error: unknown) {
      console.error(error);
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Error processing payment. Please try again later.",
      );
      setIsPaymentLoading(false);
    }
  }

  return (
    <div className="py-10 lg:mt-10">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div id="pricing" className="mx-auto max-w-4xl text-center">
          <h2 className="text-foreground mt-2 text-4xl font-bold tracking-tight sm:text-5xl">
            Buy <span className="text-primary">Circle credits</span>
          </h2>
        </div>
        <p className="text-muted-foreground mx-auto mt-6 max-w-2xl text-center text-lg leading-8">
          Purchase credits with Alipay. Credits are granted after the payment
          provider sends a verified notification.
        </p>
        {errorMessage && (
          <Alert variant="destructive" className="mt-8">
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}
        <div className="mx-auto mt-16 grid max-w-md grid-cols-1 gap-y-8 sm:mt-20">
          <Card className="ring-primary relative flex grow flex-col justify-between overflow-hidden bg-transparent! ring-2 transition-all duration-300 hover:shadow-lg">
            <CardContent className="h-full justify-between p-8 xl:p-10">
              <div className="flex items-center justify-between gap-x-4">
                <CardTitle
                  id={PaymentPlanId.Credits10}
                  className="text-foreground text-lg leading-8 font-semibold"
                >
                  {creditsPlan.name}
                </CardTitle>
              </div>
              <p className="text-muted-foreground mt-4 text-sm leading-6">
                {creditsPlan.description}
              </p>
              <p className="mt-6 flex items-baseline gap-x-1">
                <span className="text-foreground text-4xl font-bold tracking-tight">
                  {creditsPlan.price}
                </span>
              </p>
              <ul
                role="list"
                className="text-muted-foreground mt-8 space-y-3 text-sm leading-6"
              >
                {creditsPlan.features.map((feature) => (
                  <li key={feature} className="flex gap-x-3">
                    <CheckCircle
                      className="text-primary h-5 w-5 flex-none"
                      aria-hidden="true"
                    />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                onClick={handleBuyNowClick}
                aria-describedby={PaymentPlanId.Credits10}
                className="w-full"
                disabled={isPaymentLoading}
              >
                {!!user ? "Pay with Alipay" : "Log in to buy credits"}
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
