"use client";

interface ChannelBadgeProps {
  channel: string;
}

export function ChannelBadge({ channel }: ChannelBadgeProps) {
  const channelConfig = {
    browser: { label: "BROWSER", icon: "⌨" },
    sip: { label: "SIP", icon: "📞" },
    voice: { label: "VOICE", icon: "🎙" },
    web: { label: "WEB", icon: "🌐" },
  };

  const config = channelConfig[channel.toLowerCase() as keyof typeof channelConfig] || {
    label: channel.toUpperCase(),
    icon: "●",
  };

  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 border border-gray-200 text-gray-700 font-mono text-xs uppercase tracking-wider" style={{ borderRadius: "4px" }}>
      <span className="text-xs">{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
}
