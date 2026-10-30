<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { cartItemCount, cartProducts, cartTotal } from '../../data/cartStore'

const HIDDEN_ROUTES = ['cart', 'payment-success', 'payment-cancel']

const route = useRoute()
const isBumping = ref(false)

const isVisible = computed(() => cartItemCount.value > 0 && !HIDDEN_ROUTES.includes(route.name))
const itemLabel = computed(() => `${cartItemCount.value} ${cartItemCount.value === 1 ? 'item' : 'items'}`)
const formattedTotal = computed(() => `AED ${cartTotal.value.toFixed(2)}`)
const totalQuantity = computed(() =>
  cartProducts.value.reduce((total, item) => total + item.quantity, 0),
)

// The first item already gets the slide-in, so only later additions bump.
watch(totalQuantity, (quantity, previousQuantity) => {
  if (previousQuantity > 0 && quantity > previousQuantity) {
    isBumping.value = true
  }
})
</script>

<template>
  <Transition name="floating-cart">
    <RouterLink
      v-if="isVisible"
      class="floating-cart"
      :class="{ 'is-bumping': isBumping }"
      :to="{ name: 'cart' }"
      :aria-label="`View cart, ${itemLabel}, ${formattedTotal}`"
      @animationend="isBumping = false"
    >
      <svg
        class="floating-cart-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="8" cy="21" r="1" />
        <circle cx="19" cy="21" r="1" />
        <path d="M2 2h3l3 13h10l3-8H7" />
      </svg>
      <span class="floating-cart-summary">
        <strong>{{ itemLabel }}</strong>
        <small>{{ formattedTotal }}</small>
      </span>
      <span class="floating-cart-action">View cart</span>
      <svg
        class="floating-cart-chevron"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M9 6l6 6-6 6" />
      </svg>
    </RouterLink>
  </Transition>
</template>
