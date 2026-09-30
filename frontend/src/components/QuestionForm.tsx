import { FormEvent, useState } from "react";

import type { ChatRequest, StudentType } from "../services/chatApi";

export type { ChatRequest } from "../services/chatApi";

type QuestionFormProps = {
  disabled?: boolean;
  onSubmit: (request: ChatRequest) => void | Promise<void>;
};

export function QuestionForm({ disabled = false, onSubmit }: QuestionFormProps) {
  const [question, setQuestion] = useState("");
  const [studentType, setStudentType] = useState<StudentType>("unknown");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || disabled) return;

    void onSubmit({
      question: trimmedQuestion,
      student_type: studentType,
    });
  }

  return (
    <form className="question-form" onSubmit={handleSubmit}>
      <label htmlFor="student-question">What do you need to know?</label>
      <textarea
        id="student-question"
        name="question"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask about registration, deadlines, or academic policies"
        rows={4}
        disabled={disabled}
        required
      />

      <div className="question-form__controls">
        <label htmlFor="student-type">Student type</label>
        <select
          id="student-type"
          name="student_type"
          value={studentType}
          onChange={(event) => setStudentType(event.target.value as StudentType)}
          disabled={disabled}
        >
          <option value="unknown">Not sure / applies to both</option>
          <option value="undergraduate">Undergraduate</option>
          <option value="graduate">Graduate</option>
        </select>
        <button type="submit" disabled={disabled || !question.trim()}>
          {disabled ? "Checking policy..." : "Ask Purdue Policy"}
        </button>
      </div>
    </form>
  );
}
