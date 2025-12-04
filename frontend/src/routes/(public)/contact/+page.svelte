<script lang="ts">
  import { ArrowLeft, Mail, MessageSquare, Github, Linkedin, Send } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Textarea } from "$lib/components/ui/textarea";

  let name = $state("");
  let email = $state("");
  let subject = $state("");
  let message = $state("");
  let isSubmitting = $state(false);
  let submitted = $state(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    isSubmitting = true;

    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 1000));

    submitted = true;
    isSubmitting = false;
  }

  const contactMethods = [
    {
      icon: Mail,
      title: "Email",
      description: "Send us an email anytime",
      value: "contact@ragagent.io",
      href: "mailto:contact@ragagent.io"
    },
    {
      icon: MessageSquare,
      title: "Discord",
      description: "Join our community",
      value: "discord.gg/ragagent",
      href: "https://discord.gg"
    },
    {
      icon: Github,
      title: "GitHub",
      description: "Report issues or contribute",
      value: "github.com/ragagent",
      href: "https://github.com"
    }
  ];
</script>

<svelte:head>
  <title>Contact - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen bg-[#0a0a0b]">
  <!-- Header -->
  <div class="border-b border-white/10">
    <div class="container mx-auto px-4 py-6">
      <Button variant="ghost" href="/" class="text-gray-400 hover:text-white mb-4">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Home
      </Button>
      <h1 class="text-3xl md:text-4xl font-bold text-white">Contact Us</h1>
      <p class="text-gray-400 mt-2">We'd love to hear from you</p>
    </div>
  </div>

  <!-- Content -->
  <div class="container mx-auto px-4 py-12">
    <div class="max-w-5xl mx-auto">
      <div class="grid gap-12 lg:grid-cols-2">
        <!-- Contact Form -->
        <div>
          <h2 class="text-2xl font-bold text-white mb-6">Send a Message</h2>

          {#if submitted}
            <div class="p-6 rounded-2xl border border-green-500/20 bg-green-500/10">
              <h3 class="text-lg font-semibold text-green-400 mb-2">Message Sent!</h3>
              <p class="text-gray-400">Thank you for reaching out. We'll get back to you as soon as possible.</p>
              <Button
                variant="outline"
                class="mt-4 border-white/20 text-gray-300"
                onclick={() => { submitted = false; name = ""; email = ""; subject = ""; message = ""; }}
              >
                Send Another Message
              </Button>
            </div>
          {:else}
            <form onsubmit={handleSubmit} class="space-y-6">
              <div class="grid gap-4 sm:grid-cols-2">
                <div class="space-y-2">
                  <Label for="name" class="text-gray-300">Name</Label>
                  <Input
                    id="name"
                    bind:value={name}
                    placeholder="Your name"
                    required
                    class="bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="email" class="text-gray-300">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    bind:value={email}
                    placeholder="you@example.com"
                    required
                    class="bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <Label for="subject" class="text-gray-300">Subject</Label>
                <Input
                  id="subject"
                  bind:value={subject}
                  placeholder="How can we help?"
                  required
                  class="bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                />
              </div>

              <div class="space-y-2">
                <Label for="message" class="text-gray-300">Message</Label>
                <Textarea
                  id="message"
                  bind:value={message}
                  placeholder="Tell us more about your inquiry..."
                  rows={6}
                  required
                  class="bg-white/5 border-white/10 text-white placeholder:text-gray-500 resize-none"
                />
              </div>

              <Button
                type="submit"
                disabled={isSubmitting}
                class="w-full bg-indigo-600 hover:bg-indigo-700 text-white h-12"
              >
                {#if isSubmitting}
                  Sending...
                {:else}
                  <Send class="h-4 w-4 mr-2" />
                  Send Message
                {/if}
              </Button>
            </form>
          {/if}
        </div>

        <!-- Contact Methods -->
        <div>
          <h2 class="text-2xl font-bold text-white mb-6">Other Ways to Reach Us</h2>

          <div class="space-y-4">
            {#each contactMethods as method}
              <a
                href={method.href}
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-start gap-4 p-6 rounded-2xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/20 transition-all"
              >
                <div class="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                  <method.icon class="h-6 w-6 text-indigo-400" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-white">{method.title}</h3>
                  <p class="text-gray-500 text-sm mb-1">{method.description}</p>
                  <p class="text-indigo-400 text-sm">{method.value}</p>
                </div>
              </a>
            {/each}
          </div>

          <!-- Social Links -->
          <div class="mt-8 p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
            <h3 class="text-lg font-semibold text-white mb-4">Follow Us</h3>
            <div class="flex gap-4">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                class="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
              >
                <Github class="h-5 w-5 text-gray-400 hover:text-white" />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                class="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
              >
                <Linkedin class="h-5 w-5 text-gray-400 hover:text-white" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
