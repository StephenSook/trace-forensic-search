import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  getCase,
  getHealth,
  searchCases,
  type SearchRequest,
  type SearchResponse,
} from "./api";

const ok = (body: unknown): Response =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

const err = (status: number, body: unknown): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("api client", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("searchCases POSTs to /search with JSON body and returns the response", async () => {
    const fakeResponse: SearchResponse = {
      query: "eagle tattoo",
      total_matches: 1,
      latency_ms: 42,
      results: [
        {
          caseId: "UP-001",
          title: "Unidentified male, Tennessee",
          confidence: 0.91,
          threshold: "HIGH CONFIDENCE",
          stateFound: "TN",
          genderEst: "Male",
          ageRange: "30–38",
          discoveryDate: "2020-06-02",
          namusLink: null,
          matchMappings: [
            {
              queryTerm: "eagle tattoo",
              forensicField: "physical_text",
              forensicValue: "avian motif dermagraphic",
              similarity: 0.93,
            },
          ],
        },
      ],
    };
    fetchMock.mockResolvedValueOnce(ok(fakeResponse));

    const req: SearchRequest = {
      query: "eagle tattoo",
      filters: { state: "TN", sex: "Male" },
      limit: 10,
    };
    const result = await searchCases(req);

    expect(result).toEqual(fakeResponse);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/search");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(init.body as string)).toEqual(req);
  });

  it("getCase GETs /case/:id and url-encodes the id", async () => {
    fetchMock.mockResolvedValueOnce(
      ok({
        case: {
          case_id: "MP-001",
          case_type: "missing",
          sex: "Male",
          age_low: 30,
          age_high: 40,
          state: "TN",
          date_epoch: 1577836800,
          date_iso: "2020-01-01",
          physical_text: "eagle tattoo on right forearm",
          circumstances: "last seen leaving a highway rest stop",
          clothing: "dark jeans, black t-shirt",
          image_url: null,
        },
      }),
    );

    await getCase("MP/001 with spaces");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/case/MP%2F001%20with%20spaces");
    expect(init.method).toBe("GET");
    expect(init.body).toBeUndefined();
  });

  it("getHealth GETs /health", async () => {
    fetchMock.mockResolvedValueOnce(
      ok({
        status: "ok",
        vectorai_reachable: true,
        collection_exists: true,
        point_count: 60,
      }),
    );

    const res = await getHealth();

    expect(res.point_count).toBe(60);
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/health");
  });

  it("throws ApiError with FastAPI detail message on 4xx", async () => {
    fetchMock.mockResolvedValueOnce(err(422, { detail: "query: Field required" }));

    const promise = searchCases({ query: "" });
    await expect(promise).rejects.toBeInstanceOf(ApiError);

    fetchMock.mockResolvedValueOnce(err(422, { detail: "query: Field required" }));
    await expect(searchCases({ query: "" })).rejects.toMatchObject({
      name: "ApiError",
      status: 422,
      message: "query: Field required",
    });
  });

  it("throws ApiError with status-line fallback when error body has no detail", async () => {
    fetchMock.mockResolvedValueOnce(err(500, { something: "else" }));

    await expect(searchCases({ query: "x" })).rejects.toMatchObject({
      status: 500,
      message: "POST /search → 500",
    });
  });

  it("forwards AbortSignal to fetch so TanStack Query can cancel", async () => {
    const controller = new AbortController();
    fetchMock.mockResolvedValueOnce(
      ok({ query: "x", total_matches: 0, latency_ms: 1, results: [] }),
    );

    await searchCases({ query: "x" }, controller.signal);

    expect(fetchMock.mock.calls[0][1].signal).toBe(controller.signal);
  });
});
