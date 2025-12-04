<script lang="ts">
  import { ArrowLeft } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";

  const lastUpdated = "December 1, 2024";

  const sections = [
    {
      title: "1. Acceptance of Terms",
      content: `By accessing or using RAG Agent Platform, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our service.`
    },
    {
      title: "2. Description of Service",
      content: `RAG Agent Platform provides an AI-powered platform for creating custom chatbots and agents that can answer questions based on your uploaded documents. The service includes:

• Document upload and processing
• AI agent creation and configuration
• Chat interface with AI agents
• Usage analytics and monitoring
• Admin panel for account management`
    },
    {
      title: "3. User Accounts",
      content: `To use our service, you must create an account. You are responsible for:

• Providing accurate account information
• Maintaining the security of your password
• All activities that occur under your account
• Notifying us immediately of any unauthorized use`
    },
    {
      title: "4. Acceptable Use",
      content: `You agree not to use the service to:

• Upload illegal, harmful, or offensive content
• Violate any applicable laws or regulations
• Infringe on intellectual property rights
• Attempt to gain unauthorized access to systems
• Interfere with the service's operation
• Use the service for spam or phishing`
    },
    {
      title: "5. Content and Data",
      content: `You retain ownership of all content you upload to the platform. By uploading content, you grant us a limited license to process and store it for providing the service. We do not claim ownership of your data.`
    },
    {
      title: "6. Service Limitations",
      content: `Our service is provided "as is" without warranties of any kind. We do not guarantee:

• Uninterrupted or error-free service
• Accuracy of AI-generated responses
• Availability of specific AI models
• Data preservation (maintain your own backups)`
    },
    {
      title: "7. Subscription and Payment",
      content: `• Free tier: Limited features, no payment required
• Pro tier: Monthly subscription, billed automatically
• Enterprise tier: Custom pricing, contact sales

Refunds are handled on a case-by-case basis.`
    },
    {
      title: "8. Termination",
      content: `We reserve the right to suspend or terminate your account for violation of these terms. You may cancel your account at any time through your account settings.`
    },
    {
      title: "9. Changes to Terms",
      content: `We may update these terms from time to time. Continued use of the service after changes constitutes acceptance of the new terms.`
    },
    {
      title: "10. Contact",
      content: `For questions about these Terms of Service, contact us at legal@ragagent.io`
    }
  ];
</script>

<svelte:head>
  <title>Terms of Service - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen bg-[#0a0a0b]">
  <!-- Header -->
  <div class="border-b border-white/10">
    <div class="container mx-auto px-4 py-6">
      <Button variant="ghost" href="/" class="text-gray-400 hover:text-white mb-4">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Home
      </Button>
      <h1 class="text-3xl md:text-4xl font-bold text-white">Terms of Service</h1>
      <p class="text-gray-400 mt-2">Last updated: {lastUpdated}</p>
    </div>
  </div>

  <!-- Content -->
  <div class="container mx-auto px-4 py-12">
    <div class="max-w-3xl mx-auto">
      <div class="p-6 rounded-2xl border border-white/10 bg-white/[0.02] mb-8">
        <p class="text-gray-400 leading-relaxed">
          Please read these Terms of Service carefully before using RAG Agent Platform.
          These terms govern your use of our service and constitute a legal agreement between you and us.
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
