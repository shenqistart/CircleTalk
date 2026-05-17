import { useEffect } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router";

const ACCOUNT_PAGE_REDIRECT_DELAY_MS = 4000;

export default function CheckoutResultPage() {
  const navigate = useNavigate();
  const [urlSearchParams] = useSearchParams();
  const provider = urlSearchParams.get("provider");
  const status = urlSearchParams.get("status");
  const outTradeNo = urlSearchParams.get("out_trade_no");
  const tradeStatus = urlSearchParams.get("trade_status");
  const isZpayReturn =
    provider === "zpay" || !!outTradeNo || tradeStatus !== null;

  useEffect(() => {
    const accountPageRedirectTimeoutId = setTimeout(() => {
      navigate("/account");
    }, ACCOUNT_PAGE_REDIRECT_DELAY_MS);

    return () => {
      clearTimeout(accountPageRedirectTimeoutId);
    };
  }, [navigate]);

  if (!isZpayReturn && status !== "success" && status !== "canceled") {
    return <Navigate to="/account" />;
  }

  const title = getCheckoutTitle({ isZpayReturn, status });
  const description = isZpayReturn
    ? "Your payment return was received. Credits are added only after the verified payment notification arrives."
    : `You will be redirected to your account page in ${
        ACCOUNT_PAGE_REDIRECT_DELAY_MS / 1000
      } seconds...`;

  return (
    <div className="mt-10 flex flex-col items-stretch sm:mx-6 sm:items-center">
      <div className="flex flex-col gap-4 px-4 py-8 text-center shadow-xl ring-1 ring-gray-900/10 sm:max-w-md sm:rounded-lg sm:px-10 dark:ring-gray-100/10">
        <h1 className="text-xl font-semibold">{title}</h1>
        <span>{description}</span>
      </div>
    </div>
  );
}

function getCheckoutTitle({
  isZpayReturn,
  status,
}: {
  isZpayReturn: boolean;
  status: string | null;
}): string {
  if (isZpayReturn) {
    return "Payment Submitted";
  }
  return status === "success" ? "Payment Successful" : "Payment Canceled";
}
