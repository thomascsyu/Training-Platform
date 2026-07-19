/**
 * Course pricing helpers for optional special-offer (compare-at) display.
 *
 * - `price` is the amount students pay
 * - `original_price` is an optional higher compare-at price
 * - A special offer is active when original_price > price on a paid course
 */

/** Locales that render unambiguous currency signs (e.g. HK$ for HKD). */
const CURRENCY_LOCALES = {
  hkd: "en-HK",
  usd: "en-US",
  sgd: "en-SG",
  cny: "zh-CN",
  twd: "zh-TW",
  jpy: "ja-JP",
  krw: "ko-KR",
  eur: "en-IE",
  gbp: "en-GB",
  aud: "en-AU",
  cad: "en-CA",
};

function normalizeCurrency(currency) {
  return (currency || "hkd").toLowerCase() || "hkd";
}

function currencyLocale(code) {
  return CURRENCY_LOCALES[code.toLowerCase()] || undefined;
}

/**
 * Currency sign/code for form labels (e.g. "HK$", "$", "JPY").
 */
export function getCurrencySign(currency = "hkd") {
  const code = normalizeCurrency(currency).toUpperCase();
  try {
    const parts = new Intl.NumberFormat(currencyLocale(code), {
      style: "currency",
      currency: code,
      currencyDisplay: "symbol",
    }).formatToParts(0);
    return parts.find((part) => part.type === "currency")?.value || code;
  } catch {
    return code;
  }
}

export function formatCoursePrice(amount, currency = "hkd") {
  const value = Number(amount);
  const code = normalizeCurrency(currency).toUpperCase();
  const locale = currencyLocale(code);
  if (!Number.isFinite(value)) {
    try {
      return new Intl.NumberFormat(locale, {
        style: "currency",
        currency: code,
        currencyDisplay: "symbol",
      }).format(0);
    } catch {
      return `${getCurrencySign(code)} 0.00`;
    }
  }
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: code,
      currencyDisplay: "symbol",
    }).format(value);
  } catch {
    return `${getCurrencySign(code)} ${value.toFixed(2)}`;
  }
}

export function hasSpecialOffer(course) {
  if (!course || course.is_free) return false;
  const price = Number(course.price);
  const original = Number(course.original_price);
  return Number.isFinite(price) && Number.isFinite(original) && original > price;
}

export function getCoursePriceDisplay(course, currency = "hkd") {
  const price = Number(course?.price) || 0;
  if (course?.is_free) {
    return {
      isFree: true,
      hasOffer: false,
      price,
      originalPrice: null,
      priceLabel: "Free",
      originalPriceLabel: null,
    };
  }

  const offer = hasSpecialOffer(course);
  const originalPrice = offer ? Number(course.original_price) : null;
  return {
    isFree: false,
    hasOffer: offer,
    price,
    originalPrice,
    priceLabel: formatCoursePrice(price, currency),
    originalPriceLabel: offer ? formatCoursePrice(originalPrice, currency) : null,
  };
}
