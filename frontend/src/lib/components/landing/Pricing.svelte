<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Check, Sparkles } from "lucide-svelte";

  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for trying out the platform",
      features: [
        "1 AI Agent",
        "10 Documents",
        "500 queries/month",
        "GPT-3.5 Model",
        "Community Support"
      ],
      cta: "Get Started",
      ctaVariant: "outline" as const,
      popular: false
    },
    {
      name: "Pro",
      price: "$29",
      period: "per month",
      description: "For professionals and small teams",
      features: [
        "5 AI Agents",
        "100 Documents",
        "10,000 queries/month",
        "Google Gemini Models",
        "Custom Tools",
        "Priority Support",
        "API Access"
      ],
      cta: "Start Free Trial",
      ctaVariant: "default" as const,
      popular: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "contact us",
      description: "For large organizations",
      features: [
        "Unlimited Agents",
        "Unlimited Documents",
        "Unlimited queries",
        "All Models + Custom",
        "SSO & SAML",
        "Dedicated Support",
        "On-premise Option",
        "SLA Guarantee"
      ],
      cta: "Contact Sales",
      ctaVariant: "outline" as const,
      popular: false
    }
  ];
</script>

<section id="pricing" class="relative py-24 md:py-32 bg-[#0a0a0b]">
  <!-- Background -->
  <div class="absolute inset-0 bg-gradient-to-b from-transparent via-purple-500/5 to-transparent"></div>

  <div class="container relative mx-auto px-4">
    <!-- Section Header -->
    <div class="text-center max-w-3xl mx-auto mb-16">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 text-sm font-medium mb-4 border border-purple-500/20">
        Pricing
      </div>
      <h2 class="text-3xl md:text-5xl font-bold text-white mb-4">
        Simple, Transparent
        <span class="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
          Pricing
        </span>
      </h2>
      <p class="text-lg text-gray-400">
        Start free and scale as you grow. No hidden fees, no surprises.
      </p>
    </div>

    <!-- Pricing Cards -->
    <div class="grid gap-8 md:grid-cols-3 max-w-5xl mx-auto">
      {#each plans as plan}
        <div
          class="relative p-8 rounded-2xl border transition-all duration-300
            {plan.popular
              ? 'border-indigo-500/50 bg-gradient-to-b from-indigo-500/10 to-transparent'
              : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/20'}"
        >
          {#if plan.popular}
            <div class="absolute -top-4 left-1/2 -translate-x-1/2">
              <div class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-xs font-medium">
                <Sparkles class="h-3 w-3" />
                Most Popular
              </div>
            </div>
          {/if}

          <!-- Plan Header -->
          <div class="mb-6">
            <h3 class="text-xl font-semibold text-white mb-2">{plan.name}</h3>
            <div class="flex items-baseline gap-1">
              <span class="text-4xl font-bold text-white">{plan.price}</span>
              <span class="text-gray-500 text-sm">/{plan.period}</span>
            </div>
            <p class="text-gray-400 text-sm mt-2">{plan.description}</p>
          </div>

          <!-- Features -->
          <ul class="space-y-3 mb-8">
            {#each plan.features as feature}
              <li class="flex items-center gap-3 text-sm text-gray-300">
                <Check class="h-4 w-4 text-indigo-400 flex-shrink-0" />
                {feature}
              </li>
            {/each}
          </ul>

          <!-- CTA -->
          <Button
            href="/register"
            variant={plan.ctaVariant}
            class="w-full {plan.popular
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
              : 'border-white/20 text-gray-300 hover:bg-white/5 hover:text-white'}"
          >
            {plan.cta}
          </Button>
        </div>
      {/each}
    </div>
  </div>
</section>
