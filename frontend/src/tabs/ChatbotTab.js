import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ChatBubbleLeftRightIcon, 
  PaperAirplaneIcon,
  CpuChipIcon,
  UserIcon
} from '@heroicons/react/24/outline';

const ChatbotTab = ({ dataset }) => {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: 'Hello! I\'m your data analysis assistant. Load a dataset and ask me questions about your data.' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: inputMessage
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate bot response after a delay
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        sender: 'bot',
        text: `I received your message: "${inputMessage}". In a real implementation, I would analyze your dataset and provide insights based on your question.`
      };
      
      setMessages(prev => [...prev, botResponse]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-200px)]">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900 flex items-center">
          <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2 text-blue-500" />
          AI Data Assistant
        </h2>
        <div className="flex items-center text-sm text-gray-500">
          <CpuChipIcon className="h-4 w-4 mr-1" />
          <span>AI Assistant Active</span>
        </div>
      </h2>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex-1 flex flex-col">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: 'calc(100vh - 250px)' }}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start max-w-3/4 rounded-2xl p-4 ${message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'}`}>
                <div className="mr-3 flex-shrink-0">
                  {message.sender === 'user' ? (
                    <UserIcon className="h-6 w-6 text-white" />
                  ) : (
                    <ChatBubbleLeftRightIcon className="h-6 w-6 text-blue-500" />
                  )}
                </div>
                <div className="text-sm">{message.text}</div>
              </div>
            </motion.div>
          ))}
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="flex items-start max-w-3/4 rounded-2xl p-4 bg-gray-100 text-gray-800">
                <div className="mr-3 flex-shrink-0">
                  <ChatBubbleLeftRightIcon className="h-6 w-6 text-blue-500" />
                </div>
                <div className="text-sm flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Thinking...
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div className="border-t border-gray-200 p-4">
          <div className="flex items-end space-x-2">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={dataset ? "Ask a question about your dataset..." : "Load a dataset to start asking questions..."}
              disabled={!dataset || isLoading}
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
              rows="2"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || !dataset || isLoading}
              className={`h-12 w-12 flex items-center justify-center rounded-full ${!inputMessage.trim() || !dataset || isLoading ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'} text-white transition-colors duration-200`}
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-500 flex justify-between">
            <span>Ask about data patterns, statistics, or insights</span>
            <span>Status: {dataset ? 'Ready' : 'No dataset loaded'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotTab;