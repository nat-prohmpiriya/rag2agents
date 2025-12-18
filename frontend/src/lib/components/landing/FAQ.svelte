<script lang="ts">
  import { ChevronDown } from "lucide-svelte";

  const faqs = [
    {
      question: "What is RAG and how does it work?",
      answer: "RAG (Retrieval-Augmented Generation) is a technique that enhances AI responses by first retrieving relevant information from your documents, then using that context to generate accurate answers. Your AI agent searches through indexed documents to find the most relevant passages before formulating a response."
    },
    {
      question: "Which file formats are supported?",
      answer: "We support a wide range of document formats including PDF, DOCX, TXT, Markdown, CSV, and more. Documents are automatically processed and indexed for semantic search. We're constantly adding support for new formats."
    },
    {
      question: "How secure is my data?",
      answer: "Security is our top priority. All documents are encrypted at rest and in transit. We use enterprise-grade security practices including SOC 2 compliance, regular security audits, and optional on-premise deployment for Enterprise customers."
    },
    {
      question: "Can I use my own AI models?",
      answer: "Yes! We support Google Gemini models including Gemini 2.5 Pro, Gemini 2.5 Flash, and more. Enterprise customers can also bring their own fine-tuned models or self-hosted LLMs."
    },
    {
      question: "What's the difference between agents and chatbots?",
      answer: "Agents are more advanced than simple chatbots. They can use custom tools, access external APIs, perform multi-step reasoning, and take actions based on user requests. Think of agents as AI assistants that can actually do things, not just answer questions."
    },
    {
      question: "Is there a free trial?",
      answer: "Yes! Our Free plan lets you try the platform with 1 agent, 10 documents, and 500 queries per month. No credit card required. You can upgrade to Pro at any time to unlock more features and capacity."
    }
  ];

  let openIndex = $state<number | null>(null);

  function toggleFaq(index: number) {
    openIndex = openIndex === index ? null : index;
  }
</script>

<section id="faq" class="relative py-24 md:py-32 bg-[#0a0a0b]">
  <div class="container relative mx-auto px-4">
    <!-- Section Header -->
    <div class="text-center max-w-3xl mx-auto mb-16">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-sm font-medium mb-4 border border-green-500/20">
        FAQ
      </div>
      <h2 class="text-3xl md:text-5xl font-bold text-white mb-4">
        Frequently Asked
        <span class="bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-cyan-400">
          Questions
        </span>
      </h2>
      <p class="text-lg text-gray-400">
        Everything you need to know about the platform.
      </p>
    </div>

    <!-- FAQ Accordion -->
    <div class="max-w-3xl mx-auto space-y-4">
      {#each faqs as faq, index}
        <div
          class="rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden transition-all duration-300
            {openIndex === index ? 'bg-white/[0.04] border-white/20' : ''}"
        >
          <button
            class="w-full px-6 py-5 flex items-center justify-between text-left cursor-pointer"
            onclick={() => toggleFaq(index)}
          >
            <span class="font-medium text-white pr-4">{faq.question}</span>
            <ChevronDown
              class="h-5 w-5 text-gray-400 flex-shrink-0 transition-transform duration-300
                {openIndex === index ? 'rotate-180' : ''}"
            />
          </button>

          {#if openIndex === index}
            <div class="px-6 pb-5">
              <p class="text-gray-400 text-sm leading-relaxed">{faq.answer}</p>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</section>
