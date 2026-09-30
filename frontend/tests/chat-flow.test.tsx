import { afterEach, describe, expect, it, vi } from "vitest";

const chatRequest = {
  question: "What is the deadline to drop a class?",
  student_type: "undergraduate",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("chat flow", () => {
  it("submits a policy question and exposes the grounded response payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          answer: "See the official registration deadline.",
          response_type: "direct_answer",
          citations: [
            {
              source_id: "00000000-0000-0000-0000-000000000001",
              source_url: "https://example.edu/registration",
              citation_text: "Registration deadlines",
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(chatRequest),
    });
    const payload = await response.json();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(chatRequest),
      }),
    );
    expect(response.ok).toBe(true);
    expect(payload.response_type).toBe("direct_answer");
    expect(payload.answer).toBeTruthy();
    expect(payload.citations).toHaveLength(1);
  });

  it("preserves safe-referral responses without pretending they are answers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            answer: "I cannot verify an individualized exception.",
            response_type: "safe_referral",
            citations: [],
            referral: {
              office_name: "Registrar",
              referral_reason: "Contact the office for a case-specific decision.",
            },
          }),
          { status: 200 },
        ),
      ),
    );

    const response = await fetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question: "Can I get a personal exception?" }),
    });
    const payload = await response.json();

    expect(payload.response_type).toBe("safe_referral");
    expect(payload.citations).toEqual([]);
    expect(payload.referral.office_name).toBeTruthy();
  });
});
