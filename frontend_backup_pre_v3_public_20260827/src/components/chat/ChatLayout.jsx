// frontend/src/components/chat/ChatLayout.jsx
import React, { useState } from 'react';
import ChatList from './ChatList';
import ChatWindow from './ChatWindow';

function ChatLayout({ organization }) {
  const [selectedConversation, setSelectedConversation] = useState(null);

  return (
    <div className="chat-layout">
      <div className="chat-sidebar">
        <ChatList 
          organization={organization}
          onSelectConversation={setSelectedConversation}
          selectedId={selectedConversation}
        />
      </div>
      <div className="chat-main">
        <ChatWindow 
          conversationId={selectedConversation}
          organization={organization}
        />
      </div>
    </div>
  );
}

export default ChatLayout;