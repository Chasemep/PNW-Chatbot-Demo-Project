import type { Citation } from "../components/CitationList";
import type { ResponseType } from "../components/AnswerCard";

export type StudentType = "undergraduate" | "graduate" | "unknown";

export type ChatRequest = {
  question: string;
  student_type: StudentType;
};

export type ContactReferral = {
  office_name: string;
  referral_reason: string;
  contact_url?: string;
  contact_email?: string;
  contact_phone?: string;
};

export type ChatResponse = {
  answer: string;
  response_type: ResponseType;
  citations?: Citation[];
  clarification_prompt?: string;
  referral?: ContactReferral;
};

export async function postChatQuestion(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("The policy service could not process that question.");
  }

  return (await response.json()) as ChatResponse;
}
