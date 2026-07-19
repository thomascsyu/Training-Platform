import { createContext, useContext, useEffect, useState } from "react";
import { API } from "@/lib/api";

const CurrencyContext = createContext({ currency: "hkd" });

export const useCurrency = () => useContext(CurrencyContext);

export const CurrencyProvider = ({ children }) => {
  const [currency, setCurrency] = useState("hkd");

  useEffect(() => {
    let cancelled = false;

    const loadCurrency = async () => {
      try {
        const { data } = await API.get("/payments/currency");
        const code = (data?.currency || "hkd").toLowerCase();
        if (!cancelled && code) setCurrency(code);
      } catch {
        // Keep hkd fallback if the API is unavailable.
      }
    };

    loadCurrency();
    const onChanged = () => loadCurrency();
    window.addEventListener("learnhub:currency-changed", onChanged);
    return () => {
      cancelled = true;
      window.removeEventListener("learnhub:currency-changed", onChanged);
    };
  }, []);

  return (
    <CurrencyContext.Provider value={{ currency }}>
      {children}
    </CurrencyContext.Provider>
  );
};
