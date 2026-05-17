import { ReactNode } from "react";
import { PRODUCT_NAME, PRODUCT_TAGLINE } from "../shared/common";
import logo from "../client/static/logo.webp";

export function AuthPageLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-col justify-center pt-10 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <img className="h-12 w-12" src={logo} alt={PRODUCT_NAME} />
          <p className="mt-3 text-xl font-semibold text-gray-900 dark:text-white">
            {PRODUCT_NAME}
          </p>
          <p className="mt-1 px-6 text-sm text-gray-600 dark:text-gray-300">
            {PRODUCT_TAGLINE}
          </p>
        </div>
        <div className="bg-white px-4 py-8 shadow-xl ring-1 ring-gray-900/10 sm:rounded-lg sm:px-10 dark:bg-white dark:text-gray-900">
          <div className="-mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
