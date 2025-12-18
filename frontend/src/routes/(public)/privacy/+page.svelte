<script lang="ts">
  import { ArrowLeft } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";

  const lastUpdated = "December 1, 2024";

  const sections = [
    {
      title: "1. Information We Collect",
      content: `We collect information you provide directly to us, such as when you create an account, upload documents, or contact us for support. This includes:

• Account information (email, name, password)
• Documents you upload to the platform
• Chat conversations with AI agents
• Usage data and analytics`
    },
    {
      title: "2. How We Use Your Information",
      content: `We use the information we collect to:

• Provide, maintain, and improve our services
• Process documents for RAG-powered AI responses
• Monitor usage and prevent abuse
• Send you technical notices and support messages
• Respond to your comments and questions`
    },
    {
      title: "3. Data Storage and Security",
      content: `Your data security is important to us. We implement appropriate technical and organizational measures to protect your personal information:

• All data is encrypted at rest and in transit
• Documents are stored securely and isolated per user
• We use industry-standard security practices
• Regular security audits and monitoring`
    },
    {
      title: "4. Data Retention",
      content: `We retain your information for as long as your account is active or as needed to provide you services. You can request deletion of your data at any time by contacting us or through your account settings.`
    },
    {
      title: "5. Third-Party Services",
      content: `We use Google Gemini AI to process your queries. Your data sent to Google is governed by their privacy policy. We only send the minimum data necessary to provide the service.`
    },
    {
      title: "6. Your Rights",
      content: `You have the right to:

• Access your personal data
• Correct inaccurate data
• Delete your data
• Export your data
• Withdraw consent at any time`
    },
    {
      title: "7. Contact Us",
      content: `If you have any questions about this Privacy Policy, please contact us at privacy@ragagent.io`
    }
  ];
</script>

<svelte:head>
  <title>Privacy Policy - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen bg-[#0a0a0b]">
  <!-- Header -->
  <div class="border-b border-white/10">
    <div class="container mx-auto px-4 py-6">
      <Button variant="ghost" href="/" class="text-gray-400 hover:text-white mb-4">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Home
      </Button>
      <h1 class="text-3xl md:text-4xl font-bold text-white">Privacy Policy</h1>
      <p class="text-gray-400 mt-2">Last updated: {lastUpdated}</p>
    </div>
  </div>

  <!-- Content -->
  <div class="container mx-auto px-4 py-12">
    <div class="max-w-3xl mx-auto">
      <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02] mb-8">
        <p class="text-gray-400 leading-relaxed">
          At RAG Agent Platform, we take your privacy seriously. This Privacy Policy explains how we collect,
          use, disclose, and safeguard your information when you use our platform.
        </p>
      </div>

      <div class="space-y-8">
        {#each sections as section}
          <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
            <h2 class="text-xl font-semibold text-white mb-4">{section.title}</h2>
            <p class="text-gray-400 leading-relaxed whitespace-pre-line">{section.content}</p>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>
