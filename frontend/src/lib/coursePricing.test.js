import { formatCoursePrice, getCoursePriceDisplay, getCurrencySign, hasSpecialOffer } from "./coursePricing";

describe("coursePricing", () => {
  test("formats prices with currency sign", () => {
    expect(formatCoursePrice(90, "usd")).toMatch(/90/);
    expect(formatCoursePrice(90, "hkd")).toMatch(/HK\$/);
    expect(formatCoursePrice(90, "hkd")).toMatch(/90/);
    expect(formatCoursePrice("12.5", "usd")).toMatch(/12\.50|12\.5/);
  });

  test("returns unambiguous HKD sign for labels", () => {
    expect(getCurrencySign("hkd")).toBe("HK$");
    expect(getCurrencySign("HKD")).toBe("HK$");
  });

  test("detects special offer only when original_price is higher", () => {
    expect(hasSpecialOffer({ price: 90, original_price: 120, is_free: false })).toBe(true);
    expect(hasSpecialOffer({ price: 90, original_price: 90, is_free: false })).toBe(false);
    expect(hasSpecialOffer({ price: 90, original_price: 120, is_free: true })).toBe(false);
    expect(hasSpecialOffer({ price: 90, is_free: false })).toBe(false);
  });

  test("builds display model for special offer courses", () => {
    const display = getCoursePriceDisplay(
      { price: 90, original_price: 120, is_free: false },
      "hkd"
    );
    expect(display).toMatchObject({
      isFree: false,
      hasOffer: true,
      price: 90,
      originalPrice: 120,
    });
    expect(display.priceLabel).toMatch(/HK\$/);
    expect(display.priceLabel).toMatch(/90/);
    expect(display.originalPriceLabel).toMatch(/120/);
  });

  test("builds display model for free courses", () => {
    expect(getCoursePriceDisplay({ price: 0, is_free: true })).toMatchObject({
      isFree: true,
      hasOffer: false,
      priceLabel: "Free",
    });
  });
});
