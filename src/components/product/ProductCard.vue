<script setup>
import { computed } from 'vue'
import {
  addProductToCart,
  cartProducts,
  updateCartProductQuantity,
} from '../../data/cartStore'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const cartItem = computed(() => cartProducts.value.find((item) => item.id === props.product.id))
const cartQuantity = computed(() => cartItem.value?.quantity || 0)

function handleAddToCart() {
  addProductToCart(props.product)
}

function decreaseCartQuantity() {
  updateCartProductQuantity(props.product.id, cartQuantity.value - 1)
}
</script>

<template>
  <article class="product-card" :class="{ 'is-compact': compact }">
    <div class="product-image">
      <img :src="product.image" :alt="product.name" />
      <span class="product-badge">{{ product.deliveryTime }}</span>
    </div>

    <div class="product-info">
      <div class="product-meta">
        <p class="product-category">{{ product.category }}</p>
        <span class="product-rating">★ {{ product.rating }}</span>
      </div>
      <h2 class="product-name">{{ product.name }}</h2>
      <p class="product-description">{{ product.description }}</p>

      <div class="product-footer">
        <span class="product-price">
          AED {{ product.price }}
          <span v-if="product.oldPrice">AED {{ product.oldPrice }}</span>
        </span>
        <div v-if="cartQuantity" class="product-quantity-control" :aria-label="`${product.name} quantity`">
          <button
            type="button"
            :aria-label="`Decrease ${product.name} quantity`"
            @click="decreaseCartQuantity"
          >
            -
          </button>
          <span>{{ cartQuantity }}</span>
          <button
            type="button"
            :aria-label="`Increase ${product.name} quantity`"
            @click="handleAddToCart"
          >
            +
          </button>
        </div>
        <button
          v-else
          class="add-cart-button"
          type="button"
          :aria-label="`Add ${product.name} to cart`"
          @click="handleAddToCart"
        >
          <svg
            class="add-cart-icon"
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M3 5h2l2.4 10.4a2 2 0 0 0 2 1.6h6.8a2 2 0 0 0 1.9-1.4L20 9H7" />
            <circle cx="10" cy="20" r="1" />
            <circle cx="17" cy="20" r="1" />
            <path d="M12 12h4" />
            <path d="M14 10v4" />
          </svg>
        </button>
      </div>
    </div>
  </article>
</template>
