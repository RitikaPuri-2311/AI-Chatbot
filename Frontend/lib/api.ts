import type { Message } from '@/types'

export const MOCK_SESSION_ID = 'session-001'

const conversationMap: Record<string, string> = {
  // greetings
  'hey': 'Hey there! How can I help you today?',
  'hi': 'Hi! What can I assist you with?',
  'hello': 'Hello! Great to see you. What do you need help with?',
  'good morning': 'Good morning! Hope your day is going well. How can I help?',
  'good evening': 'Good evening! What can I do for you?',

  // how are you
  'how are you': 'I am doing great, thanks for asking! How about you?',
  'what are you': 'I am an AI chatbot here to assist you with your questions!',
  'who are you': 'I am your AI assistant. Ask me anything!',

  // help
  'help': 'Sure! I can answer questions, have a conversation, or assist with tasks. What do you need?',
  'what can you do ?': 'I can chat with you, answer questions, and help you think through problems!',

  // thanks
  'thanks': 'You are welcome! Anything else I can help with?',
  'thank you': 'Happy to help! Let me know if you need anything else.',
  'ok': 'Great! Feel free to ask me anything.',
  'okay': 'Alright! What else can I do for you?',
  'good': 'Great! Feel free to ask me anything.',

  // bye
  'bye': 'Goodbye! Have a wonderful day!',
  'goodbye': 'Take care! Come back anytime.',
  'see you': 'See you later! Have a great day.',
}

const fallbackReplies = [
  'That is interesting! Could you tell me more?',
  'I am not sure I fully understand. Can you rephrase that?',
  'Great point! Let me think about that.',
  'I see what you mean. Can you give me more details?',
  'Hmm, that is a good one. Could you elaborate?',
]

let fallbackIndex = 0

export async function sendMessage(content: string): Promise<Message> {
  await new Promise(r => setTimeout(r, 1200))

  const key = content.toLowerCase().trim().replace(/[!?.]/g, '')
  const reply = conversationMap[key]
    ?? fallbackReplies[fallbackIndex++ % fallbackReplies.length]

  return {
    id: Date.now().toString(),
    role: 'assistant',
    content: reply,
    createdAt: new Date().toISOString(),
  }
}

export async function getMessages(): Promise<Message[]> {
  await new Promise(r => setTimeout(r, 300))
  return []
}