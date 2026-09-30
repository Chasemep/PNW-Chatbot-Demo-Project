export type ResponseType = "direct_answer" | "clarification_needed" | "safe_referral";

type AnswerCardProps = {
  answer: string;
  responseType: ResponseType;
  referral?: {
    office_name: string;
    referral_reason: string;
  };
};

export function AnswerCard({ answer, responseType, referral }: AnswerCardProps) {
  return (
    <article className="chat-page__response" aria-live="polite">
      <p className="chat-page__response-type">{responseType.replaceAll("_", " ")}</p>
      <p className="chat-page__answer">{answer}</p>
      {referral && (
        <p className="chat-page__referral">
          Contact {referral.office_name}: {referral.referral_reason}
        </p>
      )}
    </article>
  );
}
