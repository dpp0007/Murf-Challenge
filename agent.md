Agents and handoffs
How to use agents and handoffs as part of a voice AI workflow.

Ask about this page
Ask Claude

Copy page
View markdown
Overview
Agents are the core units of a voice AI workflow. They define the instructions, tools, and reasoning behavior that drive a conversation. An agent can transfer control to other agents when different logic or capabilities are required. Create separate agents when you need distinct reasoning behavior or tool access:

Different roles: A moderator agent versus a coaching agent.
Model specialization: A lightweight triage model before escalating to a larger one.
Different permissions: An agent with payment API access versus one handling general inquiries.
Specialized contexts: Agents optimized for particular conversation phases.
Agents
Agents orchestrate the session flow — managing tools, reasoning steps, and control transfers between other agents or tasks.

Defining an agent
Use Agent.create to define a custom agent with instructions, tools, and lifecycle hooks.

PythonNode.js
from livekit.agents import Agent

class HelpfulAssistant(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful voice AI assistant.")

    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="Greet the user and ask how you can help them.")

import { voice } from '@livekit/agents';

const helpfulAssistant = voice.Agent.create({
  instructions: 'You are a helpful voice AI assistant.',
  onEnter(ctx) {
    ctx.session.generateReply({
      instructions: 'Greet the user and ask how you can help them.',
    });
  },
});

You can also create an agent inline:

PythonNode.js
agent = Agent(instructions="You are a helpful voice AI assistant.")

const agent = voice.Agent.create({
  instructions: 'You are a helpful voice AI assistant.',
});

Setting the active agent 
The active agent is the agent currently in control of the session. The initial agent is defined in the AgentSession constructor. You can change the active agent using the update_agent method in Python, or a handoff from a tool call. You can read the active agent using the current_agent property.

Specify the initial agent in the AgentSession constructor:

PythonNode.js
session = AgentSession(
    agent=CustomerServiceAgent()
    # ...
)

await session.start({
  agent: createCustomerServiceAgent(),
  room: ctx.room,
});

To set a new agent, use the update_agent method:

PythonNode.js
session.update_agent(CustomerServiceAgent())

session.updateAgent(createCustomerServiceAgent());

Agent handoffs 
A handoff transfers session control from one agent to another. You can return a different agent from within a tool call to hand off control automatically. This allows the LLM to make decisions about when a handoff should occur. For more information, see tool return value.

PythonNode.js
from livekit.agents import Agent, RunContext, function_tool

class CustomerServiceAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a friendly customer service representative. Help customers with
            general inquiries, account questions, and technical support. If a customer needs
            specialized help, transfer them to the appropriate specialist."""
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="Greet the user warmly and offer your assistance.")

    @function_tool()
    async def transfer_to_billing(self, context: RunContext):
        """Transfer the customer to a billing specialist for account and payment questions."""
        return BillingAgent(chat_ctx=self.chat_ctx), "Transferring to billing"

    @function_tool()
    async def transfer_to_technical_support(self, context: RunContext):
        """Transfer the customer to technical support for product issues and troubleshooting."""
        return TechnicalSupportAgent(chat_ctx=self.chat_ctx), "Transferring to technical support"

class BillingAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a billing specialist. Help customers with account questions, 
            payments, refunds, and billing inquiries. Be thorough and empathetic."""
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="Introduce yourself as a billing specialist and ask how you can help with their account.")

class TechnicalSupportAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a technical support specialist. Help customers troubleshoot 
            product issues, setup problems, and technical questions. Ask clarifying questions 
            to diagnose problems effectively."""
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="Introduce yourself as a technical support specialist and offer to help with any technical issues.")

import { voice, llm } from '@livekit/agents';

function createCustomerServiceAgent() {
  return voice.Agent.create({
    instructions: `You are a friendly customer service representative. Help customers with
      general inquiries, account questions, and technical support. If a customer needs
      specialized help, transfer them to the appropriate specialist.`,
    tools: [
      llm.tool({
        name: 'transferToBilling',
        description: 'Transfer the customer to a billing specialist for account and payment questions.',
        execute: async () => {
          return llm.handoff({
            agent: createBillingAgent(),
            returns: 'Transferring to billing',
          });
        },
      }),
      llm.tool({
        name: 'transferToTechnicalSupport',
        description: 'Transfer the customer to technical support for product issues and troubleshooting.',
        execute: async () => {
          return llm.handoff({
            agent: createTechnicalSupportAgent(),
            returns: 'Transferring to technical support',
          });
        },
      }),
    ],
    onEnter(ctx) {
      ctx.session.generateReply({
        instructions: 'Greet the user warmly and offer your assistance.',
      });
    },
  });
}

function createBillingAgent() {
  return voice.Agent.create({
    instructions: `You are a billing specialist. Help customers with account questions,
      payments, refunds, and billing inquiries. Be thorough and empathetic.`,
    onEnter(ctx) {
      ctx.session.generateReply({
        instructions: 'Introduce yourself as a billing specialist and ask how you can help with their account.',
      });
    },
  });
}

function createTechnicalSupportAgent() {
  return voice.Agent.create({
    instructions: `You are a technical support specialist. Help customers troubleshoot
      product issues, setup problems, and technical questions. Ask clarifying questions
      to diagnose problems effectively.`,
    onEnter(ctx) {
      ctx.session.generateReply({
        instructions: 'Introduce yourself as a technical support specialist and offer to help with any technical issues.',
      });
    },
  });
}

Passing chat_ctx to agents
In Python, BillingAgent(chat_ctx=self.chat_ctx) passes chat_ctx even though BillingAgent.__init__ doesn't explicitly accept it. This works because the Agent base class constructor accepts chat_ctx as a keyword argument. In Node.js, pass chatCtx in the Agent.create options object. For more details, see context preservation.

Chat history 
When an agent handoff occurs, an AgentHandoff item (or AgentHandoffItem in Node.js) is added to the chat context with the following properties:

old_agent_id: ID of the agent that was active before the handoff.
new_agent_id: ID of the agent that took over session control after the handoff.
Passing state
To store custom state within your session, use the userdata attribute. The type of userdata is up to you, but the recommended approach is to use a dataclass in Python or a typed interface in TypeScript.

PythonNode.js
from livekit.agents import AgentSession
from dataclasses import dataclass

@dataclass
class MySessionInfo:
    user_name: str | None = None
    age: int | None = None

interface MySessionInfo {
  userName?: string;
  age?: number;
}

To add userdata to your session, pass it in the constructor. You must also specify the type of userdata on the AgentSession itself.

PythonNode.js
session = AgentSession[MySessionInfo](
    userdata=MySessionInfo(),
    # ... tts, stt, llm, etc.
)

const session = new voice.AgentSession<MySessionInfo>({
  userData: { userName: 'Steve' },
  // ... vad, stt, tts, llm, etc.
});

Userdata is available as session.userdata, and is also available within function tools on the RunContext. The following example shows how to use userdata in an agent workflow that starts with the IntakeAgent.

PythonNode.js
class IntakeAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are an intake agent. Learn the user's name and age."""
        )
        
    @function_tool()
    async def record_name(self, context: RunContext[MySessionInfo], name: str):
        """Use this tool to record the user's name."""
        context.userdata.user_name = name
        return self._handoff_if_done()
    
    @function_tool()
    async def record_age(self, context: RunContext[MySessionInfo], age: int):
        """Use this tool to record the user's age."""
        context.userdata.age = age
        return self._handoff_if_done()
    
    def _handoff_if_done(self):
        if self.session.userdata.user_name and self.session.userdata.age:
            return CustomerServiceAgent()
        else:
            return None

class CustomerServiceAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are a friendly customer service representative.")

    async def on_enter(self) -> None:
        userdata: MySessionInfo = self.session.userdata
        await self.session.generate_reply(
            instructions=f"Greet {userdata.user_name} personally and offer your assistance."
        )

import { voice, llm } from '@livekit/agents';
import { z } from 'zod';

function handoffIfDone(ctx: voice.RunContext<MySessionInfo>) {
  if (ctx.userData.userName && ctx.userData.age) {
    return llm.handoff({
      agent: createCustomerServiceAgent(),
      returns: 'Information collected, transferring to customer service',
    });
  }
  return 'Please provide both your name and age.';
}

function createIntakeAgent() {
  return voice.Agent.create<MySessionInfo>({
    instructions: "You are an intake agent. Learn the user's name and age.",
    tools: [
      llm.tool({
        name: 'recordName',
        description: 'Use this tool to record the user\'s name.',
        parameters: z.object({
          name: z.string(),
        }),
        execute: async ({ name }, { ctx }) => {
          ctx.userData.userName = name;
          return handoffIfDone(ctx);
        },
      }),
      llm.tool({
        name: 'recordAge',
        description: 'Use this tool to record the user\'s age.',
        parameters: z.object({
          age: z.number(),
        }),
        execute: async ({ age }, { ctx }) => {
          ctx.userData.age = age;
          return handoffIfDone(ctx);
        },
      }),
    ],
  });
}

function createCustomerServiceAgent() {
  return voice.Agent.create<MySessionInfo>({
    instructions: 'You are a friendly customer service representative.',
    onEnter(ctx) {
      const userData = ctx.session.userData;
      ctx.session.generateReply({
      instructions: `Greet ${userData.userName} personally and offer your assistance.`,
      });
    },
  });
}

Context preservation 
By default, each new agent or task starts with a fresh conversation history for their LLM prompt. This applies to both tool-based handoffs and update_agent. In either case, the new agent only sees its own instructions unless you explicitly pass conversation history using chat_ctx.

To include the prior conversation, set the chat_ctx parameter in the Agent or AgentTask constructor. You can either copy the prior agent's chat_ctx, or construct a new one based on custom business logic to provide the appropriate context. For example, see Summarizing context for a helper function that summarizes the prior conversation and passes it to the next agent.

When you pass chat_ctx.copy(), the copy includes any instructions in the chat context by default. You can remove them by passing the exclude_instructions parameter so only the conversation turns carry over, not the system prompt. See the following examples.

PythonNode.js
from livekit.agents import ChatContext, function_tool, Agent

class TechnicalSupportAgent(Agent):
    def __init__(self, chat_ctx: ChatContext):
        super().__init__(
            instructions="""You are a technical support specialist. Help customers troubleshoot 
            product issues, setup problems, and technical questions.""",
            chat_ctx=chat_ctx
        )

class CustomerServiceAgent(Agent):
    # ...

    @function_tool()
    async def transfer_to_technical_support(self):
        """Transfer the customer to technical support for product issues and troubleshooting."""
        await self.session.generate_reply(instructions="Inform the customer that you're transferring them to the technical support team.")
        
        # Pass only the conversation turns, not the previous agent's instructions
        return TechnicalSupportAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True))

import { voice, llm } from '@livekit/agents';

function createTechnicalSupportAgent(chatCtx: llm.ChatContext) {
  return voice.Agent.create({
    instructions: `You are a technical support specialist. Help customers troubleshoot
      product issues, setup problems, and technical questions.`,
    chatCtx,
  });
}

function createCustomerServiceAgent(chatCtx: llm.ChatContext) {
  return voice.Agent.create({
    // ... instructions, chatCtx, etc.
    chatCtx,
    tools: [
      llm.tool({
        name: 'transferToTechnicalSupport',
        description: 'Transfer the customer to technical support for product issues and troubleshooting.',
        execute: async (_, { ctx }) => {
          await ctx.session.generateReply({
            instructions: 'Inform the customer that you\'re transferring them to the technical support team.',
          });

          return llm.handoff({
            agent: createTechnicalSupportAgent(
              ctx.session.currentAgent.chatCtx.copy({ excludeInstructions: true }),
            ),
            returns: 'Transferring to technical support team',
          });
        },
      }),
    ],
  });
}

The complete conversation history for the session is always available in session.history. For a full reference on the ChatContext API, see Chat context.

Summarizing context
When the prior conversation is long, summarize it before handoff to keep the next agent's context compact. The following helper function filters the chat context down to user and assistant turns, then uses a separate LLM call to generate a brief summary string. It allows you to pass in any LLM instance (including a lighter or faster model) independently of the main voice agent.

PythonNode.js
In Python, LLMStream.collect() awaits the full response stream and returns a CollectedResponse with text, tool_calls, and usage fields.

from livekit.agents import llm, ChatContext, function_tool, Agent, RunContext

async def summarize_session(summarizer: llm.LLM, chat_ctx: ChatContext) -> str | None:
    """Generate a brief summary of user/assistant turns using a separate LLM call."""
    summary_ctx = ChatContext()
    summary_ctx.add_message(
        role="system",
        content="Summarize the conversation between user and assistant. Keep the summary brief, touching on the main topics and outcomes.",
    )

    n_summarized = 0
    for item in chat_ctx.items:
        if item.type != "message":
            continue
        if item.role not in ("user", "assistant"):
            continue
        if item.extra.get("is_summary") is True:  # avoid summarizing previous summaries
            continue
        text = (item.text_content or "").strip()
        if text:
            summary_ctx.add_message(role="user", content=f"{item.role}: {text}")
            n_summarized += 1

    if n_summarized == 0:
        return None

    response = await summarizer.chat(chat_ctx=summary_ctx).collect()
    return response.text.strip() if response.text else None


class TriageAgent(Agent):
    # ...

    @function_tool()
    async def transfer_to_specialist(self, context: RunContext, topic: str):
        """Hand off to a specialist once triage is complete."""
        summarizer = self.session.llm  # or pass a different model, e.g. openai.LLM(model="gpt-4o-mini")
        summary = await summarize_session(summarizer, self.chat_ctx) if summarizer else None

        # Build a fresh context with only the summary for the next agent
        chat_ctx = ChatContext()
        if summary:
            chat_ctx.add_message(role="system", content=f"Prior conversation summary: {summary}")

        return SpecialistAgent(topic, chat_ctx=chat_ctx)

The following example uses collect() to accumulate the full response:


Other strategies for managing context at handoff:

Truncate: Pass chat_ctx.copy().truncate(max_items=6) to carry only the last few turns.
Userdata summary: Store key facts in userdata and inject a brief summary (for example, as YAML or JSON) as a system message when the next agent starts.
Overriding plugins 
You can override any of the plugins used in the session by setting the corresponding attributes in your Agent or AgentTask constructor. This allows you to customize the behavior and properties of the active agent or task in the session by modifying the prompt, TTS, LLM, STT plugins, and more.

For instance, you can change the voice for a specific agent by overriding the tts attribute:

PythonNode.js
from livekit.agents import Agent, inference

class CustomerServiceManager(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a customer service manager who can handle escalated issues.",
            tts=inference.TTS(model="inworld/inworld-tts-2", voice="Ashley")
        )

import { voice, inference } from '@livekit/agents';

function createCustomerServiceManager() {
  return voice.Agent.create({
    instructions: 'You are a customer service manager who can handle escalated issues.',
    tts: new inference.TTS({ model: 'inworld/inworld-tts-2', voice: 'Ashley' }),
  });
}

Updating models at runtime 
Only Available in
Python
To replace a model on the active agent without a full handoff, call update_options() on the Agent. The method takes an stt, vad, llm, or tts parameter. It changes only the models that you pass. The stt, llm, and tts parameters also accept an inference model string, the same as the constructor. To turn off a model, pass None. This overrides the session default.

If the agent is active, the STT and VAD change immediately. The LLM and TTS change at the next generation or synthesis. If the agent isn't active, the new model replaces the stored model. The agent then uses the new model at the next start. The call is synchronous.

The following tool switches the active agent to a more capable LLM for complex requests:

from livekit.agents import Agent, RunContext, function_tool

class Assistant(Agent):
    @function_tool()
    async def escalate_to_advanced_model(self, context: RunContext) -> str:
        """Switch to a more capable model for complex requests."""
        self.update_options(llm="openai/gpt-5.3-chat-latest")
        return "Switched to the advanced model."

Realtime models can't be replaced on an active agent
While the agent is active, you can't set the llm parameter to a RealtimeModel. You also can't replace a RealtimeModel with a different model. Both calls raise a RuntimeError. A realtime model opens a session with the model provider at agent start. That session can't move to a different model. To change it, use update_agent and hand off to a new agent. The method checks the models before it changes them. If a call fails, the agent stays the same.

Choosing a runtime update method 
You can change models or options in three ways while a session runs. Each way applies at a different level. Agent.update_options() and a model's own update_options() have the same name, but they do different things. Agent.update_options() gives the agent a different model, for example a new TTS model. A model's own update_options() keeps the same model and changes its settings, for example the temperature of an LLM.

Method	Scope	Use it to
Agent.update_options()	Same agent, different model	Replace the STT, VAD, LLM, or TTS on the active agent.
AgentSession.update_agent()	New agent instance	Hand off to a different agent, including its instructions and tools.
<model>.update_options()	Same model instance	Change provider options on a model, such as the temperature or model string on an inference.LLM.