<script setup>
import { computed } from 'vue'
import {
  cartItemCount,
  cartProducts,
  cartTotal,
  removeProductFromCart,
  updateCartProductQuantity,
} from '../data/cartStore'

defineEmits(['continueShopping'])

const deliveryFee = computed(() => (cartTotal.value >= 60 || !cartProducts.value.length ? 0 : 6))
const handlingFee = computed(() => (cartProducts.value.length ? 2 : 0))
const payableTotal = computed(() => cartTotal.value + deliveryFee.value + handlingFee.value)
</script>

<template>
  <section class="cart-page">
    <div class="cart-heading">
      <div>
        <p class="section-label">Cart</p>
        <h1>Your cart</h1>
        <p class="cart-heading-copy">
          {{ cartItemCount }} items ready for quick delivery.
        </p>
      </div>
      <button class="section-link" type="button" @click="$emit('continueShopping')">
        Continue shopping
      </button>
    </div>

    <div v-if="cartProducts.length" class="cart-layout">
      <div class="cart-item-list">
        <article
          v-for="item in cartProducts"
          :key="item.id"
          class="cart-item"
        >
          <img class="cart-item-image" :src="item.image" :alt="item.name" />
          <div class="cart-item-info">
            <h2>{{ item.name }}</h2>
            <p>AED {{ item.price }} each</p>
            <strong>AED {{ item.price * item.quantity }}</strong>
          </div>
          <div class="cart-quantity">
            <button
              type="button"
              aria-label="Decrease quantity"
              @click="updateCartProductQuantity(item.id, item.quantity - 1)"
            >
              -
            </button>
            <span>{{ item.quantity }}</span>
            <button
              type="button"
              aria-label="Increase quantity"
              @click="updateCartProductQuantity(item.id, item.quantity + 1)"
            >
              +
            </button>
          </div>
          <button
            class="cart-remove-button"
            type="button"
            @click="removeProductFromCart(item.id)"
          >
            Remove
          </button>
        </article>
      </div>

      <aside class="cart-summary">
        <div class="delivery-card">
          <span class="delivery-icon" aria-hidden="true">⌁</span>
          <div>
            <h2>Delivery in 12-18 min</h2>
            <p>Fresh items will be packed after checkout.</p>
          </div>
        </div>

        <div class="cart-summary-panel">
          <h2>Bill details</h2>
          <div class="cart-summary-row">
            <span>Items total</span>
            <strong>AED {{ cartTotal }}</strong>
          </div>
          <div class="cart-summary-row">
            <span>Delivery fee</span>
            <strong>{{ deliveryFee ? `AED ${deliveryFee}` : 'FREE' }}</strong>
          </div>
          <div class="cart-summary-row">
            <span>Handling fee</span>
            <strong>AED {{ handlingFee }}</strong>
          </div>
          <div class="cart-summary-total">
            <span>To pay</span>
            <strong>AED {{ payableTotal }}</strong>
          </div>
          <button class="checkout-button" type="button">Proceed to checkout</button>
        </div>
      </aside>
    </div>

    <div v-else class="empty-cart">
      <div class="empty-cart-icon" aria-hidden="true">⌂</div>
      <h2>Your cart is empty</h2>
      <p>Add fresh products from nearby stores and checkout in minutes.</p>
      <button class="primary-dark-button" type="button" @click="$emit('continueShopping')">
        Start shopping
      </button>
    </div>
  </section>
</template>
