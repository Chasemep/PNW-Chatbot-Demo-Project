type ClarificationPromptProps = {
  prompt: string;
};

export function ClarificationPrompt({ prompt }: ClarificationPromptProps) {
  return <p className="chat-page__follow-up">{prompt}</p>;
}
