import { useState } from "react";

import { AnswerCard } from "../components/AnswerCard";
import { CitationList } from "../components/CitationList";
import { ClarificationPrompt } from "../components/ClarificationPrompt";
import { SafeReferralCard } from "../components/SafeReferralCard";
import { ChatRequest, QuestionForm } from "../components/QuestionForm";
import { ChatResponse, postChatQuestion } from "../services/chatApi";
import "../styles/chat.css";

export function ChatPage() {
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitQuestion(request: ChatRequest) {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      setResponse(await postChatQuestion(request));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The policy service is unavailable.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="chat-page">
      <section className="chat-page__hero" aria-labelledby="chat-title">
        <p className="chat-page__eyebrow">Purdue Northwest · Policy desk</p>
        <h1 id="chat-title">Find the rule before you act.</h1>
        <p className="chat-page__intro">
          Ask a question and get an answer grounded in current Purdue Northwest sources.
        </p>
      </section>

      <section className="chat-page__workspace" aria-label="Policy question">
        <QuestionForm disabled={isLoading} onSubmit={submitQuestion} />

        {isLoading && (
          <p className="chat-page__status" role="status">
            Searching approved policy sources...
          </p>
        )}
        {error && (
          <p className="chat-page__error" role="alert">
            {error}
          </p>
        )}
        {response && (
          <>
            <AnswerCard
              answer={response.answer}
              responseType={response.response_type}
              referral={response.referral}
            />
            {response.referral && (
              <SafeReferralCard
                officeName={response.referral.office_name}
                reason={response.referral.referral_reason}
                contactUrl={response.referral.contact_url}
              />
            )}
            {response.clarification_prompt && (
              <ClarificationPrompt prompt={response.clarification_prompt} />
            )}
            <CitationList citations={response.citations ?? []} />
          </>
        )}
      </section>
    </main>
  );
}
