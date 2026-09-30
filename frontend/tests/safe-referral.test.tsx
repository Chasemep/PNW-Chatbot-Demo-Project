import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("safe referral UI contract", () => {
  it("shows referral details and no citations for unreliable information", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            answer: "I cannot verify an individualized decision.",
            response_type: "safe_referral",
            citations: [],
            referral: {
              office_name: "Registrar",
              referral_reason: "Contact the Registrar for a case-specific decision.",
              contact_url: "https://example.edu/registrar",
            },
          }),
          { status: 200 },
        ),
      ),
    );

    const response = await fetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question: "Can I get an exception?" }),
    });
    const payload = await response.json();

    expect(payload.response_type).toBe("safe_referral");
    expect(payload.citations).toEqual([]);
    expect(payload.referral.office_name).toBe("Registrar");
    expect(payload.referral.contact_url).toContain("example.edu");
  });
});
