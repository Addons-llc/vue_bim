<script setup>
import { computed } from 'vue'
import {
  cartItemCount,
  cartProducts,
  cartTotal,
  updateCartProductQuantity,
} from '../data/cartStore'

defineEmits(['continueShopping'])

const deliveryFee = computed(() => (cartTotal.value >= 60 || !cartProducts.value.length ? 0 : 6))
const handlingFee = computed(() => (cartProducts.value.length ? 2 : 0))
const payableTotal = computed(() => cartTotal.value + deliveryFee.value + handlingFee.value)
const itemSavings = computed(() =>
  cartProducts.value.reduce((total, item) => {
    if (!item.oldPrice || item.oldPrice <= item.price) {
      return total
    }

    return total + (item.oldPrice - item.price) * item.quantity
  }, 0),
)
</script>

<template>
  <section class="cart-page" @click="$emit('continueShopping')">
    <aside class="cart-drawer" aria-label="Shopping cart" @click.stop>
      <header class="cart-drawer-header">
        <button
          class="cart-back-button"
          type="button"
          aria-label="Close cart"
          @click="$emit('continueShopping')"
        >
          &larr;
        </button>
        <h1>My Cart</h1>
        <button class="cart-share-button" type="button">
          <span aria-hidden="true">♺</span>
          Share
        </button>
      </header>

      <div v-if="cartProducts.length" class="cart-drawer-body">
        <section class="cart-drawer-card cart-item-card" aria-label="Cart items">
          <article
            v-for="item in cartProducts"
            :key="item.id"
            class="cart-drawer-item"
          >
            <img class="cart-drawer-item-image" :src="item.image" :alt="item.name" />
            <div class="cart-drawer-item-info">
              <h2>{{ item.name }}</h2>
              <p>{{ item.description || 'Fresh item' }}</p>
              <strong>AED {{ item.price }}</strong>
              <span v-if="item.oldPrice" class="cart-drawer-old-price">
                AED {{ item.oldPrice }}
              </span>
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
          </article>
        </section>

        <section class="cart-drawer-card cart-bill-card" aria-label="Bill details">
          <h2>Bill details</h2>
          <div class="cart-summary-row">
            <span>Items total</span>
            <strong>
              <span v-if="itemSavings" class="cart-drawer-savings">
                Saved AED {{ itemSavings }}
              </span>
              AED {{ cartTotal }}
            </strong>
          </div>
          <div class="cart-summary-row">
            <span>Delivery charge</span>
            <strong>{{ deliveryFee ? `AED ${deliveryFee}` : 'FREE' }}</strong>
          </div>
          <div class="cart-summary-row">
            <span>Handling charge</span>
            <strong>AED {{ handlingFee }}</strong>
          </div>
          <div class="cart-summary-total">
            <span>Grand total</span>
            <strong>AED {{ payableTotal }}</strong>
          </div>
        </section>

        <section class="cart-drawer-card cart-policy-card">
          <h2>Cancellation Policy</h2>
          <p>
            Orders cannot be cancelled once packed for delivery. In case of unexpected
            delays, a refund will be provided, if applicable.
          </p>
        </section>
      </div>

      <div v-else class="cart-drawer-empty">
        <div class="empty-cart-icon" aria-hidden="true">⌂</div>
        <h2>Your cart is empty</h2>
        <p>Add fresh products from nearby stores and checkout in minutes.</p>
        <button class="primary-dark-button" type="button" @click="$emit('continueShopping')">
          Start shopping
        </button>
      </div>

      <footer v-if="cartProducts.length" class="cart-checkout-bar">
        <div>
          <strong>AED {{ payableTotal }}</strong>
          <span>TOTAL</span>
        </div>
        <button class="cart-login-button" type="button">
          Login to Proceed
          <span aria-hidden="true">›</span>
        </button>
      </footer>
    </aside>
  </section>
</template>
