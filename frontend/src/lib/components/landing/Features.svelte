<script lang="ts">
  import { Bot, FileText, Wrench, Layers, BarChart3, Shield } from "lucide-svelte";

  const features = [
    {
      icon: Bot,
      title: "Agent Builder",
      description: "Create custom AI agents with unique personalities and capabilities. Configure behavior, tone, and expertise areas.",
      color: "indigo"
    },
    {
      icon: FileText,
      title: "RAG / Documents",
      description: "Upload PDFs, docs, and text files. Your agent learns from your data and provides accurate, sourced answers.",
      color: "cyan"
    },
    {
      icon: Wrench,
      title: "Custom Tools",
      description: "Extend your agents with custom tools. Connect APIs, databases, and external services seamlessly.",
      color: "purple"
    },
    {
      icon: Layers,
      title: "Multi-Model Support",
      description: "Powered by Google Gemini models. Choose from Gemini Pro, Flash, and more without changing your workflow.",
      color: "pink"
    },
    {
      icon: BarChart3,
      title: "Usage Analytics",
      description: "Track queries, token usage, and costs in real-time. Optimize performance and manage budgets effectively.",
      color: "green"
    },
    {
      icon: Shield,
      title: "Admin Panel",
      description: "Manage users, permissions, and system settings. Enterprise-ready with role-based access control.",
      color: "orange"
    }
  ];

  const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
    indigo: { bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-indigo-500/20" },
    cyan: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/20" },
    purple: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/20" },
    pink: { bg: "bg-pink-500/10", text: "text-pink-400", border: "border-pink-500/20" },
    green: { bg: "bg-green-500/10", text: "text-green-400", border: "border-green-500/20" },
    orange: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/20" }
  };
</script>

<section id="features" class="relative py-24 md:py-32 bg-[#0a0a0b]">
  <!-- Background -->
  <div class="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-500/5 to-transparent"></div>

  <div class="container relative mx-auto px-4">
    <!-- Section Header -->
    <div class="text-center max-w-3xl mx-auto mb-16">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-sm font-medium mb-4 border border-indigo-500/20">
        Features
      </div>
      <h2 class="text-3xl md:text-5xl font-bold text-white mb-4">
        Everything You Need to Build
        <span class="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
          Intelligent Agents
        </span>
      </h2>
      <p class="text-lg text-gray-400">
        A complete platform for creating, deploying, and managing AI agents that understand your business.
      </p>
    </div>

    <!-- Feature Cards Grid -->
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {#each features as feature, index}
        {@const colors = colorClasses[feature.color]}
        <div
          class="group relative p-6 rounded-2xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-300 hover:border-white/20"
          style="animation-delay: {index * 100}ms"
        >
          <!-- Icon -->
          <div class="mb-4 inline-flex p-3 rounded-xl {colors.bg} {colors.border} border">
            <feature.icon class="h-6 w-6 {colors.text}" />
          </div>

          <!-- Content -->
          <h3 class="text-xl font-semibold text-white mb-2 group-hover:text-indigo-300 transition-colors">
            {feature.title}
          </h3>
          <p class="text-gray-400 text-sm leading-relaxed">
            {feature.description}
          </p>

          <!-- Hover Glow -->
          <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
        </div>
      {/each}
    </div>
  </div>
</section>
