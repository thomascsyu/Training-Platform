import { formatCoursePrice, getCoursePriceDisplay, hasSpecialOffer } from "./coursePricing";

describe("coursePricing", () => {
  test("formats prices with two decimals", () => {
    expect(formatCoursePrice(90)).toBe("$90.00");
    expect(formatCoursePrice("12.5")).toBe("$12.50");
  });

  test("detects special offer only when original_price is higher", () => {
    expect(hasSpecialOffer({ price: 90, original_price: 120, is_free: false })).toBe(true);
    expect(hasSpecialOffer({ price: 90, original_price: 90, is_free: false })).toBe(false);
    expect(hasSpecialOffer({ price: 90, original_price: 120, is_free: true })).toBe(false);
    expect(hasSpecialOffer({ price: 90, is_free: false })).toBe(false);
  });

  test("builds display model for special offer courses", () => {
    expect(getCoursePriceDisplay({ price: 90, original_price: 120, is_free: false })).toEqual({
      isFree: false,
      hasOffer: true,
      price: 90,
      originalPrice: 120,
      priceLabel: "$90.00",
      originalPriceLabel: "$120.00",
    });
  });

  test("builds display model for free courses", () => {
    expect(getCoursePriceDisplay({ price: 0, is_free: true })).toMatchObject({
      isFree: true,
      hasOffer: false,
      priceLabel: "Free",
    });
  });
});
