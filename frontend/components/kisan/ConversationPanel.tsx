'use client';

import React, { useEffect, useRef, useState } from 'react';
import { type ReceivedMessage } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import { useLanguage } from '@/contexts/LanguageContext';
import { ArrowUpRight } from 'lucide-react';

interface ConversationPanelProps {
  messages: ReceivedMessage[];
  canSend?: boolean;
  onSendMessage?: (message: string) => Promise<void> | void;
}

export function ConversationPanel({ messages, canSend = false, onSendMessage }: ConversationPanelProps) {
  const { t } = useLanguage();
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);

  const hasMessages = Array.isArray(messages) && messages.length > 0;
  const trimmedDraft = draft.trim();
  const isDisabled = !canSend || isSending || trimmedDraft.length === 0;

  useEffect(() => {
    if (scrollRef.current && hasMessages) {
      const el = scrollRef.current;
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, hasMessages]);

  const handleSend = async () => {
    if (isDisabled || !onSendMessage) return;

    try {
      setIsSending(true);
      await onSendMessage(trimmedDraft);
      setDraft('');
      inputRef.current?.focus();
    } catch (error) {
      console.error('Failed to send text message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  };

  return (
    <aside
      aria-label="Conversation panel"
      className="w-full
        rounded-[26px] border border-white/45 bg-white/28 px-5 py-5
        shadow-[0_18px_48px_-30px_rgba(27,94,32,0.3)] backdrop-blur-[20px]
        animate-soft-in flex flex-col h-[520px]"
    >
      {/* Header with green top border */}
      <div className="flex flex-col pb-3 border-b border-white/50 mb-2">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-[17px] font-semibold leading-tight text-[#1B5E20]">
              {t.conversation}
            </div>
            <div className="mt-0.5 flex items-center gap-2 text-[11px] font-medium text-[#546E7A]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#2E7D32]" />
              <span>{hasMessages ? t.messageCount(messages.length) : t.live}</span>
            </div>
          </div>
        </div>
        {/* Green decorative line at top */}
        <div className="h-[3px] w-[45%] bg-gradient-to-r from-[#1B5E20] to-[#2E7D32] rounded-full -mx-5 mt-2" />
      </div>

      {/* Messages area */}
      <div
        ref={scrollRef}
        className="mt-2 flex-1 overflow-y-auto thin-scroll pr-2 space-y-2.5"
      >
        {!hasMessages ? (
          <EmptyConversation t={t} />
        ) : (
          <div className="flex flex-col gap-2.5 pb-1">
            {messages.map((m, idx) => (
              <MessageBubble key={`${m.id ?? idx}-${idx}`} message={m} t={t} />
            ))}
          </div>
        )}
      </div>

      {/* Input area */}
      <form
        className="mt-3 border-t border-white/45 pt-3"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSend();
        }}
      >
        <div className="flex items-end gap-2 rounded-[18px] border border-white/60 bg-white/48 p-2 shadow-[0_8px_24px_-20px_rgba(27,94,32,0.22)] backdrop-blur-md">
          <textarea
            ref={inputRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!canSend || isSending}
            rows={1}
            placeholder={t.typeMessagePlaceholder}
            className="min-h-[42px] max-h-24 flex-1 resize-none border-0 bg-transparent px-1 py-2 text-[13.5px] leading-5 text-[#263238] placeholder:text-[#78909C] focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={isDisabled}
            aria-label={t.sendMessage}
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#2E7D32] text-white shadow-[0_10px_22px_-12px_rgba(27,94,32,0.35)] transition-all duration-150 hover:bg-[#1B5E20] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55"
          >
            <ArrowUpRight className="h-4.5 w-4.5" strokeWidth={2.4} />
          </button>
        </div>
      </form>

      {/* Hidden AgentChatTranscript so the package state tracking still works */}
      <div className="hidden" aria-hidden="true">
        <AgentChatTranscript messages={messages} />
      </div>
    </aside>
  );
}

function EmptyConversation({ t }: { t: ReturnType<typeof useLanguage>['t'] }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 py-4 text-center animate-soft-in">
      <p className="mb-1 text-sm font-semibold text-[#1B5E20]">
        {t.conversationEmpty}
      </p>
      <p className="max-w-[280px] text-[12.5px] leading-snug text-[#546E7A]">
        {t.conversationEmptySubtitle}
      </p>
    </div>
  );
}

function MessageBubble({
  message,
  t,
}: {
  message: ReceivedMessage;
  t: ReturnType<typeof useLanguage>['t'];
}) {
  const isUser = !!message.from?.isLocal;

  const rawContent: any = (message as any).message ?? (message as any).content;
  let text = '';
  if (typeof rawContent === 'string') {
    text = rawContent;
  } else if (Array.isArray(rawContent)) {
    text = rawContent
      .map((c: any) =>
        typeof c === 'string' ? c : c && typeof c === 'object' && 'text' in c ? c.text : ''
      )
      .filter(Boolean)
      .join(' ');
  } else if (rawContent && typeof rawContent === 'object') {
    text = String((rawContent as any).text ?? (rawContent as any).content ?? '');
  }

  if (!text?.trim()) {
    if (!isUser) {
      return (
        <div className="flex flex-col animate-soft-in">
          <span className="text-[11px] font-semibold text-[#1B5E20] mb-1 ml-1">
            {t.agent}
          </span>
          <div className="msg-agent self-start px-3.5 py-2 rounded-2xl rounded-tl-md bg-gray-100">
            <div className="flex gap-1.5 items-center h-4">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2E7D32]/60 animate-bounce" />
              <span
                className="w-1.5 h-1.5 rounded-full bg-[#2E7D32]/50 animate-bounce"
                style={{ animationDelay: '0.15s' }}
              />
              <span
                className="w-1.5 h-1.5 rounded-full bg-[#2E7D32]/40 animate-bounce"
                style={{ animationDelay: '0.3s' }}
              />
            </div>
          </div>
        </div>
      );
    }
    return null;
  }

  return (
    <div
      className={`flex flex-col animate-soft-in ${isUser ? 'items-end' : 'items-start'}`}
    >
      <span
        className={`text-[11px] font-semibold mb-1 mx-1 ${
          isUser ? 'text-[#37474F]' : 'text-[#1B5E20]'
        }`}
      >
        {isUser ? t.you : t.agent}
      </span>
      <div
        className={`max-w-[90%] px-3.5 py-2.5 rounded-2xl
          text-[13.5px] leading-relaxed text-[#263238] whitespace-pre-wrap break-words
          shadow-[0_2px_8px_-4px_rgba(27,94,32,0.15)]
          ${isUser ? 'msg-user rounded-tr-md bg-green-100/40' : 'msg-agent rounded-tl-md bg-white/45'}`}
      >
        {text}
      </div>
    </div>
  );
}
