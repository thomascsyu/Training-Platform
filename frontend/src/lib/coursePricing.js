/**
 * Course pricing helpers for optional special-offer (compare-at) display.
 *
 * - `price` is the amount students pay
 * - `original_price` is an optional higher compare-at price
 * - A special offer is active when original_price > price on a paid course
 */

export function formatCoursePrice(amount) {
  const value = Number(amount);
  if (!Number.isFinite(value)) return "$0.00";
  return `$${value.toFixed(2)}`;
}

export function hasSpecialOffer(course) {
  if (!course || course.is_free) return false;
  const price = Number(course.price);
  const original = Number(course.original_price);
  return Number.isFinite(price) && Number.isFinite(original) && original > price;
}

export function getCoursePriceDisplay(course) {
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
    priceLabel: formatCoursePrice(price),
    originalPriceLabel: offer ? formatCoursePrice(originalPrice) : null,
  };
}
