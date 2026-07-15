export const AI_SUGGESTED_PROMPTS = [
  {
    title: 'Explain a concept',
    prompt: 'Explain how large language models work in simple terms.',
  },
  {
    title: 'Write code',
    prompt: 'Write a Python function to validate an email address.',
  },
  {
    title: 'Brainstorm ideas',
    prompt: 'Give me 5 creative marketing ideas for a SaaS product launch.',
  },
  {
    title: 'Summarize text',
    prompt: 'Summarize the key benefits of using AI assistants in customer support.',
  },
] as const

export const PERSONA_OPTIONS = [
  { value: 'default', label: 'Default', emoji: '🤖' },
  { value: 'support', label: 'Support', emoji: '🎧' },
  { value: 'weather', label: 'Weather', emoji: '🌤️' },
  { value: 'code_reviewer', label: 'Code Review', emoji: '💻' },
  { value: 'document_analyst', label: 'Doc Analyst', emoji: '📄' },
] as const
