import React, { useState, useRef, useEffect } from 'react';

// Define the shape of a chat message
export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

interface MeetingChatProps {
  onSendMessage: (message: string) => Promise<string | void>;
  isThinking: boolean;
}

export default function MeetingChat({ onSendMessage, isThinking }: MeetingChatProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'ai', content: 'Hi! Ask me anything about the meeting so far.' }
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    const userMsg = input.trim();
    setInput('');
    
    // 1. Add user message to UI immediately
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    
    // 2. Trigger the backend call and wait for the AI's answer
    const aiResponse = await onSendMessage(userMsg);
    
    // 3. If we got an answer, add the AI's bubble to the screen!
    if (aiResponse) {
      setMessages(prev => [...prev, { role: 'ai', content: aiResponse }]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-100 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          Chat with Meeting
          <span className="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full font-medium">
            Mistral Large 3
          </span>
        </h2>
      </div>

      {/* Message History Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div 
              className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-none shadow-sm' 
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* The "Thinking" Animation */}
        {isThinking && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 text-gray-800 p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-2">
              <span className="flex gap-1">
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={handleSubmit} className="flex gap-2 relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g., What did Faris say about the timeline?"
            className="flex-1 px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-gray-50"
            disabled={isThinking}
          />
          <button
            type="submit"
            disabled={!input.trim() || isThinking}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}