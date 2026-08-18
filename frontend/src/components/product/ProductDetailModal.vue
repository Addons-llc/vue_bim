<script setup>
import { computed, ref, watch } from 'vue'
import {
  addProductToCart,
  cartProducts,
  updateCartProductQuantity,
} from '../../data/cartStore'

const props = defineProps({
  product: {
    type: Object,
    default: null,
  },
})

defineEmits(['close'])

const activeImageIndex = ref(0)

const cartItem = computed(() =>
  props.product
    ? cartProducts.value.find((item) => item.id === props.product.id)
    : null,
)
const productQuantity = computed(() => cartItem.value?.quantity || 0)

function buildProductImageVariants(image) {
  if (!image) {
    return []
  }

  const imageVariants = new Set([image])

  try {
    const imageUrl = new URL(image)

    ;[
      { width: '900', crop: 'center' },
      { width: '900', crop: 'edges' },
    ].forEach((variant) => {
      const variantUrl = new URL(imageUrl)
      variantUrl.searchParams.set('w', variant.width)
      variantUrl.searchParams.set('crop', variant.crop)
      imageVariants.add(variantUrl.toString())
    })
  } catch {
    imageVariants.add(image)
  }

  return Array.from(imageVariants)
}

const productImages = computed(() => {
  if (!props.product) {
    return []
  }

  const images = props.product.images?.length
    ? props.product.images
    : buildProductImageVariants(props.product.image)

  return images.filter(Boolean)
})
const defaultProductSize = computed(() => {
  const rawSize = props.product?.selectedSize || props.product?.size || props.product?.customSize || props.product?.custom_size || ''

  if (Array.isArray(rawSize)) {
    return rawSize.map((size) => String(size).trim()).find(Boolean) || ''
  }

  return String(rawSize)
    .split(/\r?\n|[|,;/]+/)
    .map((size) => size.trim())
    .find(Boolean) || String(rawSize).trim()
})

const productDetails = computed(() => {
  if (!props.product) {
    return []
  }

  if (props.product.details?.length) {
    return props.product.details
  }

  return [
    { label: 'Pack size', value: props.product.description },
    { label: 'Category', value: props.product.category },
    { label: 'Delivery', value: props.product.deliveryTime || '18 min' },
  ].filter((detail) => detail.value)
})

function selectProductDetailImage(index) {
  activeImageIndex.value = index
}

function moveProductDetailImage(direction) {
  const imageCount = productImages.value.length

  if (!imageCount) {
    return
  }

  activeImageIndex.value = (activeImageIndex.value + direction + imageCount) % imageCount
}

function addSelectedProductToCart() {
  if (props.product) {
    addProductToCart({
      ...props.product,
      selectedSize: defaultProductSize.value,
    })
  }
}

function decreaseSelectedProductQuantity() {
  if (props.product) {
    updateCartProductQuantity(props.product.id, productQuantity.value - 1)
  }
}

watch(
  () => props.product?.id,
  () => {
    activeImageIndex.value = 0
  },
)
</script>

<template>
  <div
    v-if="product"
    class="product-detail-backdrop"
    role="presentation"
    @click="$emit('close')"
  >
    <article
      class="product-detail-panel"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="`product-detail-title-${product.id}`"
      @click.stop
    >
      <button
        class="product-detail-close"
        type="button"
        aria-label="Close product details"
        @click="$emit('close')"
      >
        &times;
      </button>

      <div class="product-detail-media">
        <div class="product-detail-main-frame">
          <img
            class="product-detail-main-image"
            :src="productImages[activeImageIndex]"
            :alt="product.name"
          />
          <template v-if="productImages.length > 1">
            <button
              class="product-detail-image-button is-left"
              type="button"
              :aria-label="`Show previous ${product.name} image`"
              @click="moveProductDetailImage(-1)"
            >
              ‹
            </button>
            <button
              class="product-detail-image-button is-right"
              type="button"
              :aria-label="`Show next ${product.name} image`"
              @click="moveProductDetailImage(1)"
            >
              ›
            </button>
            <span class="product-detail-image-count">
              {{ activeImageIndex + 1 }} / {{ productImages.length }}
            </span>
          </template>
        </div>
        <div v-if="productImages.length > 1" class="product-detail-thumbnails">
          <button
            v-for="(image, index) in productImages"
            :key="image"
            class="product-detail-thumbnail"
            :class="{ 'is-active': activeImageIndex === index }"
            type="button"
            :aria-label="`Show ${product.name} image ${index + 1}`"
            @click="selectProductDetailImage(index)"
          >
            <img :src="image" :alt="`${product.name} preview ${index + 1}`" />
          </button>
        </div>
      </div>

      <div class="product-detail-content">
        <p class="product-detail-category">{{ product.category }}</p>
        <h2 :id="`product-detail-title-${product.id}`">{{ product.name }}</h2>
        <p class="product-detail-description">{{ product.description }}</p>

        <div class="product-detail-meta">
          <span>★ {{ product.rating }}</span>
          <span>{{ product.deliveryTime || '18 min' }}</span>
          <span>{{ product.category }}</span>
        </div>

        <dl v-if="productDetails.length" class="product-detail-list">
          <div
            v-for="detail in productDetails"
            :key="detail.label"
            class="product-detail-row"
          >
            <dt>{{ detail.label }}</dt>
            <dd>{{ detail.value }}</dd>
          </div>
        </dl>

        <div class="product-detail-footer">
          <span class="product-detail-price">
            AED {{ product.price }}
            <span v-if="product.oldPrice">AED {{ product.oldPrice }}</span>
          </span>

          <div
            v-if="productQuantity"
            class="product-quantity-control"
            :aria-label="`${product.name} quantity`"
          >
            <button
              type="button"
              :aria-label="`Decrease ${product.name} quantity`"
              @click="decreaseSelectedProductQuantity"
            >
              -
            </button>
            <span>{{ productQuantity }}</span>
            <button
              type="button"
              :aria-label="`Increase ${product.name} quantity`"
              @click="addSelectedProductToCart"
            >
              +
            </button>
          </div>
          <button
            v-else
            class="product-detail-add-button"
            type="button"
            @click="addSelectedProductToCart"
          >
            Add to cart
          </button>
        </div>
      </div>
    </article>
  </div>
</template>
