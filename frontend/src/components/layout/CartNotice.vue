<script setup>
import { cartNotice } from '../../data/cartStore'
</script>

<template>
  <Transition name="cart-notice">
    <div v-if="cartNotice.message" :key="cartNotice.id" class="cart-notice" role="status">
      {{ cartNotice.message }}
    </div>
  </Transition>
</template>

<style scoped>
.cart-notice {
  position: fixed;
  bottom: calc(96px + env(safe-area-inset-bottom, 0px));
  left: 50%;
  z-index: 220;
  width: max-content;
  max-width: calc(100vw - 32px);
  border-radius: 14px;
  padding: 10px 18px;
  background: #b91c1c;
  box-shadow: var(--shadow-md);
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  text-align: center;
  transform: translateX(-50%);
}

.cart-notice-enter-active,
.cart-notice-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.cart-notice-enter-from,
.cart-notice-leave-to {
  opacity: 0;
  transform: translate(-50%, 12px);
}
</style>
