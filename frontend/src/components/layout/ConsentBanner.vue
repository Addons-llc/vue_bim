<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getConsentChoice, isAnalyticsEnabled, setConsentChoice } from '../../analytics'

// Shown once, only when GA is configured for this site and the visitor hasn't chosen yet.
const isVisible = ref(false)

onMounted(() => {
  isVisible.value = isAnalyticsEnabled() && getConsentChoice() === null
})

function choose(choice) {
  setConsentChoice(choice)
  isVisible.value = false
}
</script>

<template>
  <section v-if="isVisible" class="consent-banner" role="region" aria-label="Cookie consent">
    <p class="consent-banner-text">
      We use analytics cookies to understand how the store is used and improve it.
      <RouterLink to="/privacy-policy">Privacy Policy</RouterLink>
    </p>
    <div class="consent-banner-actions">
      <button type="button" class="consent-banner-button" @click="choose('denied')">Decline</button>
      <button type="button" class="consent-banner-button is-primary" @click="choose('granted')">
        Accept
      </button>
    </div>
  </section>
</template>

<style scoped>
.consent-banner {
  position: fixed;
  right: 16px;
  bottom: 16px;
  left: 16px;
  z-index: 100;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
  justify-content: space-between;
  max-width: 720px;
  margin: 0 auto;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  color: #111827;
  font-size: 14px;
  line-height: 1.45;
}

.consent-banner-text {
  flex: 1 1 260px;
  margin: 0;
}

.consent-banner-text a {
  color: #00785f;
  font-weight: 600;
}

.consent-banner-actions {
  display: flex;
  gap: 8px;
}

.consent-banner-button {
  min-height: 40px;
  padding: 0 18px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  color: #111827;
  font: inherit;
  font-weight: 650;
  cursor: pointer;
}

.consent-banner-button.is-primary {
  border-color: #078b20;
  background: #078b20;
  color: #fff;
}

.consent-banner-button:focus-visible {
  outline: 3px solid #93c5fd;
  outline-offset: 2px;
}

/* Clear the bottom tab bar on phones and tablets. */
@media (max-width: 1024px) {
  .consent-banner {
    bottom: calc(76px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
