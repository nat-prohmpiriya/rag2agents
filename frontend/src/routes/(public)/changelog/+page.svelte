<script lang="ts">
  import { ArrowLeft } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";

  const releases = [
    {
      version: "v1.2.0",
      date: "2024-12-01",
      type: "feature",
      changes: [
        "Added multi-model support (Google Gemini)",
        "New usage analytics dashboard",
        "Improved document processing speed by 40%",
        "Added custom tools builder"
      ]
    },
    {
      version: "v1.1.0",
      date: "2024-11-15",
      type: "feature",
      changes: [
        "Introduced RAG-powered document chat",
        "Added PDF, DOCX, and TXT file support",
        "New agent configuration panel",
        "Real-time token usage tracking"
      ]
    },
    {
      version: "v1.0.1",
      date: "2024-11-01",
      type: "fix",
      changes: [
        "Fixed authentication token refresh issue",
        "Improved error handling for file uploads",
        "Performance optimizations for chat interface"
      ]
    },
    {
      version: "v1.0.0",
      date: "2024-10-20",
      type: "release",
      changes: [
        "Initial release of RAG Agent Platform",
        "Basic agent creation and management",
        "Document upload and indexing",
        "Chat interface with AI agents",
        "User authentication and authorization"
      ]
    }
  ];

  const typeColors: Record<string, { bg: string; text: string }> = {
    feature: { bg: "bg-green-500/10", text: "text-green-400" },
    fix: { bg: "bg-yellow-500/10", text: "text-yellow-400" },
    release: { bg: "bg-indigo-500/10", text: "text-indigo-400" }
  };
</script>

<svelte:head>
  <title>Changelog - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen bg-[#0a0a0b]">
  <!-- Header -->
  <div class="border-b border-white/10">
    <div class="container mx-auto px-4 py-6">
      <Button variant="ghost" href="/" class="text-gray-400 hover:text-white mb-4">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Home
      </Button>
      <h1 class="text-3xl md:text-4xl font-bold text-white">Changelog</h1>
      <p class="text-gray-400 mt-2">All notable changes to RAG Agent Platform</p>
    </div>
  </div>

  <!-- Content -->
  <div class="container mx-auto px-4 py-12">
    <div class="max-w-3xl mx-auto">
      <div class="relative">
        <!-- Timeline Line -->
        <div class="absolute left-0 md:left-8 top-0 bottom-0 w-px bg-white/10"></div>

        <!-- Releases -->
        <div class="space-y-12">
          {#each releases as release}
            {@const colors = typeColors[release.type]}
            <div class="relative pl-8 md:pl-20">
              <!-- Timeline Dot -->
              <div class="absolute left-0 md:left-8 -translate-x-1/2 w-3 h-3 rounded-full bg-indigo-500 border-4 border-[#0a0a0b]"></div>

              <!-- Release Card -->
              <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
                <div class="flex flex-wrap items-center gap-3 mb-4">
                  <span class="text-xl font-bold text-white">{release.version}</span>
                  <span class="px-2 py-1 rounded-full text-xs font-medium {colors.bg} {colors.text} capitalize">
                    {release.type}
                  </span>
                  <span class="text-sm text-gray-500">{release.date}</span>
                </div>

                <ul class="space-y-2">
                  {#each release.changes as change}
                    <li class="flex items-start gap-2 text-gray-400 text-sm">
                      <span class="text-indigo-400 mt-1">•</span>
                      {change}
                    </li>
                  {/each}
                </ul>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
</div>
