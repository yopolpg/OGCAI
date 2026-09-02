import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { CategorizedDrawer } from './components/CategorizedDrawer';
import { ChatWorkspace } from './components/ChatWorkspace';
import { api } from './services/api';
import { Conversation, Message, ModelInfo, RouteDecision } from './types';

export const App: React.FC = () => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null); // null = auto
  const [activeModelName, setActiveModelName] = useState<string>('Qwen 2.5 Coder 7B');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);

  // Streaming State
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingRouteInfo, setStreamingRouteInfo] = useState<RouteDecision | null>(null);

  // 1. Initial Load
  useEffect(() => {
    const init = async () => {
      try {
        const [modelsList, convList] = await Promise.all([
          api.getModels(),
          api.listConversations()
        ]);
        setModels(modelsList || []);
        setConversations(convList || []);

        if (convList && convList.length > 0) {
          const firstId = convList[0].id;
          setActiveConversationId(firstId);
          const fullConv = await api.getConversation(firstId);
          setMessages(fullConv.messages || []);
        }
      } catch (e) {
        console.error('Initialization error:', e);
      }
    };
    init();
  }, []);

  // 2. Select Conversation
  const handleSelectConversation = async (id: string) => {
    setActiveConversationId(id);
    try {
      const fullConv = await api.getConversation(id);
      setMessages(fullConv.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  // 3. New Conversation
  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation('การสนทนาใหม่');
      setConversations([newConv, ...conversations]);
      setActiveConversationId(newConv.id);
      setMessages([]);
    } catch (e) {
      console.error(e);
    }
  };

  // 4. Delete Conversation
  const handleDeleteConversation = async (id: string) => {
    try {
      await api.deleteConversation(id);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);
      if (activeConversationId === id) {
        if (remaining.length > 0) {
          handleSelectConversation(remaining[0].id);
        } else {
          setActiveConversationId(null);
          setMessages([]);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // 5. Send Message & Stream
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    let convId = activeConversationId;
    // Create new conversation if none active
    if (!convId) {
      try {
        const newConv = await api.createConversation(text.slice(0, 30));
        if (newConv && newConv.id) {
          convId = newConv.id;
          setConversations((prev) => [newConv, ...prev.filter(c => c.id !== newConv.id)]);
          setActiveConversationId(convId);
        }
      } catch (err) {
        console.error('Failed to create conversation:', err);
      }
    }

    // Append user message to UI
    const userMsg: Message = {
      id: `temp_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMsg]);

    // Prepare stream
    setIsStreaming(true);
    setStreamingContent('');
    setStreamingRouteInfo(null);

    let accumulated = '';
    let currentModel = selectedModel || 'qwen2.5-coder:7b';

    await api.streamChat({
      message: text,
      conversationId: convId || undefined,
      model: selectedModel || undefined,
      onMetadata: (meta: any) => {
        setStreamingRouteInfo(meta);
        const resolvedModel = meta.selected_model || meta.model || 'qwen2.5-coder:7b';
        currentModel = resolvedModel;
        setActiveModelName(resolvedModel);
      },
      onToken: (token) => {
        accumulated += token;
        setStreamingContent(accumulated);
      },
      onDone: () => {
        const assistantMsg: Message = {
          id: `msg_${Date.now()}`,
          role: 'assistant',
          content: accumulated,
          model: currentModel,
          timestamp: new Date().toISOString()
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setIsStreaming(false);
        setStreamingContent('');
        setStreamingRouteInfo(null);
        // Refresh conversation list so newly created or updated conversation appears in drawer
        api.listConversations().then((list) => setConversations(list || [])).catch(() => {});
      },
      onError: (err) => {
        const errorMsg: Message = {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ เกิดข้อผิดพลาดในการตอบกลับ: ${err}`,
          model: 'error',
          timestamp: new Date().toISOString()
        };
        setMessages((prev) => [...prev, errorMsg]);
        setIsStreaming(false);
        setStreamingContent('');
        setStreamingRouteInfo(null);
      }
    });
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#090d16] text-slate-100 overflow-hidden font-sans">
      {/* Top Navigation Bar */}
      <Header
        models={models}
        selectedModel={selectedModel}
        activeModelName={activeModelName}
        onSelectModel={setSelectedModel}
        isDrawerOpen={isDrawerOpen}
        onToggleDrawer={() => setIsDrawerOpen(!isDrawerOpen)}
      />

      {/* Main Workspace with Collapsible Categorized Drawer */}
      <div className="flex-1 flex overflow-hidden relative">
        <CategorizedDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
        />

        <ChatWorkspace
          messages={messages}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          streamingRouteInfo={streamingRouteInfo}
          onSendMessage={handleSendMessage}
          onSelectSuggestion={handleSendMessage}
        />
      </div>
    </div>
  );
};
export default App;
