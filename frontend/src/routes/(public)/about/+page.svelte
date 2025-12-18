<script lang="ts">
  import { ArrowLeft, Github, Linkedin, Mail } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";

  const techStack = [
    { category: "Frontend", items: ["SvelteKit", "Svelte 5", "TypeScript", "Tailwind CSS", "shadcn-svelte"] },
    { category: "Backend", items: ["FastAPI", "Python 3.12", "SQLAlchemy", "PostgreSQL", "pgvector"] },
    { category: "AI/ML", items: ["LiteLLM", "Google Gemini", "RAG"] },
    { category: "Infrastructure", items: ["Docker", "Redis", "Celery", "S3 Storage"] }
  ];
</script>

<svelte:head>
  <title>About - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen bg-[#0a0a0b]">
  <!-- Header -->
  <div class="border-b border-white/10">
    <div class="container mx-auto px-4 py-6">
      <Button variant="ghost" href="/" class="text-gray-400 hover:text-white mb-4">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Home
      </Button>
      <h1 class="text-3xl md:text-4xl font-bold text-white">About</h1>
      <p class="text-gray-400 mt-2">Learn more about RAG Agent Platform</p>
    </div>
  </div>

  <!-- Content -->
  <div class="container mx-auto px-4 py-12">
    <div class="max-w-4xl mx-auto space-y-16">
      <!-- About Project -->
      <section>
        <h2 class="text-2xl font-bold text-white mb-6">About This Project</h2>
        <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
          <p class="text-gray-400 leading-relaxed mb-4">
            RAG Agent Platform is a full-stack AI application that enables users to create custom AI agents
            powered by their own documents. Using Retrieval-Augmented Generation (RAG), agents can answer
            questions with accurate, sourced information from uploaded documents.
          </p>
          <p class="text-gray-400 leading-relaxed mb-4">
            This project was built as a portfolio demonstration showcasing modern web development practices,
            AI integration, and enterprise-ready architecture patterns.
          </p>
          <p class="text-gray-400 leading-relaxed">
            Key features include multi-model support (Google Gemini), custom tool integration,
            real-time usage analytics, and a comprehensive admin panel for user and system management.
          </p>
        </div>
      </section>

      <!-- Tech Stack -->
      <section>
        <h2 class="text-2xl font-bold text-white mb-6">Tech Stack</h2>
        <div class="grid gap-4 md:grid-cols-2">
          {#each techStack as stack}
            <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
              <h3 class="text-lg font-semibold text-white mb-3">{stack.category}</h3>
              <div class="flex flex-wrap gap-2">
                {#each stack.items as item}
                  <span class="px-3 py-1 rounded-full text-sm bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {item}
                  </span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      </section>

      <!-- Features -->
      <section>
        <h2 class="text-2xl font-bold text-white mb-6">Key Features</h2>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
            <h3 class="text-lg font-semibold text-white mb-2">RAG-Powered Chat</h3>
            <p class="text-gray-400 text-sm">Upload documents and chat with AI that answers from your knowledge base with source citations.</p>
          </div>
          <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
            <h3 class="text-lg font-semibold text-white mb-2">Multi-Model Support</h3>
            <p class="text-gray-400 text-sm">Powered by Google Gemini for intelligent AI conversations.</p>
          </div>
          <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
            <h3 class="text-lg font-semibold text-white mb-2">Custom Tools</h3>
            <p class="text-gray-400 text-sm">Extend agent capabilities with custom tools and API integrations.</p>
          </div>
          <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
            <h3 class="text-lg font-semibold text-white mb-2">Usage Analytics</h3>
            <p class="text-gray-400 text-sm">Track queries, tokens, and costs in real-time with detailed analytics.</p>
          </div>
        </div>
      </section>

      <!-- Contact -->
      <section>
        <h2 class="text-2xl font-bold text-white mb-6">Get In Touch</h2>
        <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
          <p class="text-gray-400 mb-6">
            Interested in this project or want to discuss opportunities? Feel free to reach out!
          </p>
          <div class="flex flex-wrap gap-4">
            <Button variant="outline" class="border-white/20 text-gray-300 hover:bg-white/5">
              <Github class="h-4 w-4 mr-2" />
              GitHub
            </Button>
            <Button variant="outline" class="border-white/20 text-gray-300 hover:bg-white/5">
              <Linkedin class="h-4 w-4 mr-2" />
              LinkedIn
            </Button>
            <Button variant="outline" class="border-white/20 text-gray-300 hover:bg-white/5">
              <Mail class="h-4 w-4 mr-2" />
              Email
            </Button>
          </div>
        </div>
      </section>
    </div>
  </div>
</div>
