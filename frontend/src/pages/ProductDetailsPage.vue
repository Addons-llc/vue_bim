<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  addProductToCart,
  cartProducts,
  updateCartProductQuantity,
} from '../data/cartStore'
import { getSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'
import { getProductById } from '../api/productApi'

const route = useRoute()
const product = ref(null)
const isLoading = ref(false)
const loadError = ref('')
const hasProductDetailLoaded = ref(false)
const activeImageIndex = ref(0)
const isProductDescriptionExpanded = ref(false)
const selectedProductSize = ref('')

const productId = computed(() => String(route.params.productId || ''))
const productQuantity = computed(() => {
  if (!product.value) {
    return 0
  }

  return cartProducts.value.find((item) => item.id === product.value.id)?.quantity || 0
})
const supplierName = computed(() =>
  product.value?.supplierName || product.value?.supplier || 'Supplier not set',
)
const sourceListing = computed(() => product.value?.sourceListing || null)
const brandName = computed(() =>
  product.value?.brand
  || (sourceListing.value?.type === 'brand' ? sourceListing.value.name : '')
  || '',
)
const ratingStars = computed(() => {
  const rating = Math.round(Number(product.value?.rating || 0))

  return '★'.repeat(Math.min(rating, 5)) || '★★★★★'
})
const productDescription = computed(() => product.value?.description || '')
const isProductDescriptionLong = computed(() => productDescription.value.length > 120)
const productSizeOptions = computed(() => {
  const rawSize = product.value?.customSize || product.value?.custom_size || ''

  if (Array.isArray(rawSize)) {
    return rawSize.map((size) => String(size).trim()).filter(Boolean)
  }

  const sizeText = String(rawSize || '').trim()

  if (!sizeText) {
    return []
  }

  const splitSizes = sizeText
    .split(/\r?\n|[|,;/]+/)
    .map((size) => size.trim())
    .filter(Boolean)

  return splitSizes.length > 1 ? splitSizes : [sizeText]
})
const selectedProductSizeLabel = computed(() =>
  selectedProductSize.value || productSizeOptions.value[0] || '',
)

function mergeProductDetails(cachedProduct, loadedProduct) {
  if (!cachedProduct) {
    return loadedProduct
  }

  return {
    ...loadedProduct,
    image: loadedProduct.image || cachedProduct.image,
    bannerImage: loadedProduct.bannerImage || cachedProduct.bannerImage,
    images: loadedProduct.images?.length ? loadedProduct.images : cachedProduct.images,
    price: loadedProduct.price || cachedProduct.price,
    oldPrice: loadedProduct.oldPrice || cachedProduct.oldPrice,
    supplierName: loadedProduct.supplierName || cachedProduct.supplierName,
    supplier: loadedProduct.supplier || cachedProduct.supplier,
    brand: loadedProduct.brand || cachedProduct.brand,
    supplierDetails: loadedProduct.supplierDetails || cachedProduct.supplierDetails,
    sourceListing: cachedProduct.sourceListing || loadedProduct.sourceListing,
    deliveryTime: loadedProduct.deliveryTime || cachedProduct.deliveryTime,
    reviewCount: loadedProduct.reviewCount || cachedProduct.reviewCount,
    stockQuantity: loadedProduct.stockQuantity || cachedProduct.stockQuantity,
    inStock: loadedProduct.inStock ?? cachedProduct.inStock,
    customDeliverySlots: loadedProduct.customDeliverySlots ?? cachedProduct.customDeliverySlots,
    customSize: loadedProduct.customSize || cachedProduct.customSize || loadedProduct.custom_size || cachedProduct.custom_size,
  }
}

const productImages = computed(() => {
  if (!product.value) {
    return []
  }

  const images = product.value.images?.length
    ? product.value.images
    : [product.value.bannerImage || product.value.image].filter(Boolean)

  return images.filter(Boolean)
})
const activeProductImage = computed(() =>
  productImages.value[activeImageIndex.value]
    || product.value?.bannerImage
    || product.value?.image
    || '',
)

const productDetails = computed(() => {
  if (!product.value) {
    return []
  }

  if (product.value.details?.length) {
    const details = [...product.value.details]

    if (selectedProductSizeLabel.value && !details.some((detail) => detail.label === 'Size')) {
      details.push({ label: 'Size', value: selectedProductSizeLabel.value })
    }

    return details
  }

  return [
    sourceListing.value?.name
      ? { label: sourceListing.value.label || 'Selected from', value: sourceListing.value.name }
      : null,
    { label: 'Supplier', value: supplierName.value },
    sourceListing.value?.storeCode
      ? { label: 'Store code', value: sourceListing.value.storeCode }
      : null,
    selectedProductSizeLabel.value
      ? { label: 'Size', value: selectedProductSizeLabel.value }
      : null,
    { label: 'Category', value: product.value.category },
  ].filter((detail) => detail?.value)
})

async function loadProduct() {
  if (!productId.value) {
    loadError.value = 'Product not found.'
    return
  }

  hasProductDetailLoaded.value = false
  const cachedProduct = getSelectedProduct(productId.value)
  product.value = cachedProduct
  isLoading.value = !cachedProduct
  loadError.value = ''

  try {
    const loadedProduct = await getProductById(productId.value)
    if (!loadedProduct) {
      product.value = null
      loadError.value = 'Product not found.'
      return
    }

    product.value = mergeProductDetails(cachedProduct, loadedProduct)
    activeImageIndex.value = 0
    isProductDescriptionExpanded.value = false
    hasProductDetailLoaded.value = true
  } catch (error) {
    if (!cachedProduct) {
      product.value = null
      loadError.value = error.message || 'Unable to load product details.'
    }
  } finally {
    isLoading.value = false
  }
}

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
  if (product.value) {
    addProductToCart({
      ...product.value,
      selectedSize: selectedProductSizeLabel.value,
    })
  }
}

function decreaseSelectedProductQuantity() {
  if (product.value) {
    updateCartProductQuantity(product.value.id, productQuantity.value - 1)
  }
}

function selectProductSize(size) {
  selectedProductSize.value = size
}

function toggleProductDescription() {
  isProductDescriptionExpanded.value = !isProductDescriptionExpanded.value
}

function rememberSupplierSelection() {
  saveSelectedSupplier({
    name: supplierName.value,
    details: product.value?.supplierDetails,
    product: product.value,
  })
}

watch(productId, loadProduct, { immediate: true })

watch(productSizeOptions, (sizes) => {
  if (!sizes.length) {
    selectedProductSize.value = ''
    return
  }

  if (!sizes.includes(selectedProductSize.value)) {
    selectedProductSize.value = sizes[0]
  }
}, { immediate: true })
</script>

<template>
  <p v-if="isLoading && !product" class="dashboard-message">Loading product details...</p>
  <p v-else-if="loadError" class="dashboard-message">{{ loadError }}</p>

  <template v-else-if="product">
    <nav class="product-detail-breadcrumbs" aria-label="Product location">
      <RouterLink :to="{ name: 'home' }">Home</RouterLink>
      <RouterLink
        :to="{
          name: 'home',
          query: product.category ? { category: product.category } : {},
        }"
      >
        {{ product.category || 'Products' }}
      </RouterLink>
      <strong>{{ product.name }}</strong>
    </nav>

    <article
      class="product-detail-screen"
      :aria-labelledby="`product-detail-title-${product.id}`"
    >
      <div
        class="product-detail-media"
        :class="{ 'has-thumbnails': productImages.length > 1 }"
      >
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

        <div class="product-detail-main-frame">
          <img
            class="product-detail-main-image"
            :src="activeProductImage"
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
      </div>

      <div class="product-detail-content">
        <RouterLink
          v-if="brandName"
          class="product-detail-category product-detail-brand-link"
          :to="{ name: 'brand-details', params: { brandName } }"
        >
          {{ brandName }}
        </RouterLink>
        <p v-else class="product-detail-category">{{ supplierName }}</p>
        <!-- Source listing is kept in productDetails below; avoid duplicating Brand under the brand link. -->
        <!--
        <p v-if="sourceListing" class="product-detail-category">
          {{ sourceListing.label }}: {{ sourceListing.name }}
        </p>
        -->
        <h2 :id="`product-detail-title-${product.id}`">{{ product.name }}</h2>

        <div class="product-detail-rating-row">
          <span>{{ product.rating }}</span>
          <span class="product-detail-stars">{{ ratingStars }}</span>
          <a href="#product-details">3 Ratings</a>
        </div>

        <div class="product-detail-price-row">
          <span class="product-detail-price">
            <span class="product-detail-currency">AED</span>
            {{ product.price }}
          </span>
        </div>

        <section v-if="productSizeOptions.length" class="product-detail-section product-size-section">
          <h3>Size</h3>
          <div class="product-size-options" role="group" aria-label="Choose product size">
            <button
              v-for="size in productSizeOptions"
              :key="size"
              class="product-size-option"
              :class="{ 'is-selected': selectedProductSizeLabel === size }"
              type="button"
              @click="selectProductSize(size)"
            >
              {{ size }}
            </button>
          </div>
        </section>

        <p
          class="product-detail-description"
          :class="{ 'is-collapsed': !isProductDescriptionExpanded && isProductDescriptionLong }"
        >
          {{ productDescription }}
        </p>
        <button
          v-if="isProductDescriptionLong"
          class="product-description-toggle"
          type="button"
          @click="toggleProductDescription"
        >
          {{ isProductDescriptionExpanded ? 'Show less' : 'Show more' }}
        </button>

        <dl v-if="productDetails.length" id="product-details" class="product-detail-list">
          <div
            v-for="detail in productDetails"
            :key="detail.label"
            class="product-detail-row"
          >
            <dt>{{ detail.label }}</dt>
            <dd>{{ detail.value }}</dd>
          </div>
        </dl>
      </div>

      <aside class="product-detail-purchase" aria-label="Purchase options">
        <RouterLink
          class="product-detail-seller-card"
          :to="{ name: 'supplier-details', params: { supplierName } }"
          @click="rememberSupplierSelection"
        >
          <span class="product-detail-seller-mark">{{ supplierName.slice(0, 2).toUpperCase() }}</span>
          <div>
            <span>Sold by</span>
            <strong>{{ supplierName }}</strong>
            <p>Not enough ratings to show</p>
          </div>
        </RouterLink>

        <div class="product-detail-trust-list">
          <span>↩ Easy and hassle free returns</span>
          <span>♢ Secure payments</span>
        </div>

        <div class="product-detail-footer">
          <div>
            <span class="product-detail-total-label">Total</span>
            <strong class="product-detail-total-price">
              AED {{ product.price }}
            </strong>
          </div>

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
      </aside>
    </article>
  </template>
</template>
