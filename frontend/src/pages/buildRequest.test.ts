import { describe, expect, it } from "vitest";
import { buildRequest, type SearchFormState } from "./Index";

const EMPTY_FORM: SearchFormState = {
  query: "",
  sex: "",
  state: "",
  ageLow: "",
  ageHigh: "",
  dateFrom: "",
  dateTo: "",
};

describe("buildRequest", () => {
  it("query-only form produces no filters key", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "eagle tattoo" });
    expect(req).toEqual({ query: "eagle tattoo", filters: undefined, limit: 10 });
  });

  it("all filters populated builds complete request", () => {
    const req = buildRequest({
      query: "tattoo",
      sex: "Male",
      state: "TN",
      ageLow: "30",
      ageHigh: "40",
      dateFrom: "2019-01-01",
      dateTo: "2020-12-31",
    });
    expect(req).toEqual({
      query: "tattoo",
      filters: {
        sex: "Male",
        state: "TN",
        age_low: 30,
        age_high: 40,
        date_from: "2019-01-01",
        date_to: "2020-12-31",
      },
      limit: 10,
    });
  });

  it("age values are parsed as integers, not strings", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "x", ageLow: "30", ageHigh: "45" });
    expect(req.filters?.age_low).toBe(30);
    expect(req.filters?.age_high).toBe(45);
    expect(typeof req.filters?.age_low).toBe("number");
  });

  it("age value '0' is correctly included as 0", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "x", ageLow: "0" });
    expect(req.filters?.age_low).toBe(0);
  });

  it("sex filter passes through the exact string value", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "x", sex: "Female" });
    expect(req.filters?.sex).toBe("Female");
  });

  it("partial filters omit only empty fields", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "x", state: "CA", dateFrom: "2020-01-01" });
    expect(req.filters).toEqual({ state: "CA", date_from: "2020-01-01" });
  });

  it("limit is always 10", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "x" });
    expect(req.limit).toBe(10);
  });

  it("NaN from garbage ageLow is omitted, not sent as null", () => {
    const req = buildRequest({ ...EMPTY_FORM, query: "x", ageLow: "abc" });
    expect(req.filters).toBeUndefined();
  });
});
