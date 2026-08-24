<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  addProductToCart,
  cartProducts,
  updateCartProductQuantity,
} from '../data/cartStore'
import { getCustomerToSupplierDistanceKm, LOCATION_UPDATED_EVENT } from '../api/deliveryEta'
import { getSelectedProduct, saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'
import { getProductById, getProductVariants } from '../api/productApi'

const route = useRoute()
const router = useRouter()
const product = ref(null)
const productVariants = ref([])
const isLoading = ref(false)
const isLoadingVariants = ref(false)
const loadError = ref('')
const hasProductDetailLoaded = ref(false)
const activeImageIndex = ref(0)
const isProductDescriptionExpanded = ref(false)
const selectedProductSize = ref('')
const selectedVariantAttributes = ref({})
const supplierDistanceKm = ref(null)
const isCheckingDeliverability = ref(false)

const MAX_DELIVERABLE_DISTANCE_KM = 20

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
const variantTemplateId = computed(() =>
  product.value?.variantOf || (product.value?.hasVariants ? product.value.id : ''),
)
const selectedVariantId = computed(() => product.value?.id || '')
const hasProductVariants = computed(() => productVariants.value.length > 0)
const showVariantDropdowns = computed(() =>
  hasProductVariants.value && product.value?.variantBasedOn === 'Item Attribute',
)
const isOutOfDeliveryRange = computed(() =>
  Number.isFinite(supplierDistanceKm.value) && supplierDistanceKm.value > MAX_DELIVERABLE_DISTANCE_KM,
)
const deliveryStatusMessage = computed(() => {
  if (isCheckingDeliverability.value) {
    return 'Checking delivery availability...'
  }

  if (isOutOfDeliveryRange.value) {
    return 'Not deliverable to this location.'
  }

  if (Number.isFinite(supplierDistanceKm.value) && supplierDistanceKm.value > 0) {
    return `Deliverable within ${supplierDistanceKm.value.toFixed(1).replace(/\\.0$/, '')} km.`
  }

  return ''
})
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
const variantAttributeGroups = computed(() => {
  const groups = []
  const seenAttributes = new Set()
  const variantRecords = productVariants.value.length
    ? productVariants.value
    : (product.value ? [product.value] : [])

  variantRecords.forEach((variant) => {
    ;(variant.variantAttributes || []).forEach((attributeRow) => {
      const attributeName = String(attributeRow.attribute || '').trim()
      const attributeValue = String(attributeRow.value || '').trim()

      if (!attributeName || !attributeValue) {
        return
      }

      let group = groups.find((entry) => entry.name === attributeName)
      if (!group) {
        group = { name: attributeName, options: [] }
        groups.push(group)
      }

      if (!group.options.includes(attributeValue)) {
        group.options.push(attributeValue)
      }

      seenAttributes.add(attributeName)
    })
  })

  return groups.filter((group) => seenAttributes.has(group.name))
})

function mergeProductDetails(cachedProduct, loadedProduct) {
  if (!cachedProduct) {
    return loadedProduct
  }

  return {
    ...loadedProduct,
    image: loadedProduct.image || cachedProduct.image,
    bannerImage: loadedProduct.bannerImage || cachedProduct.bannerImage,
    attachmentImages: loadedProduct.attachmentImages?.length
      ? loadedProduct.attachmentImages
      : (cachedProduct.attachmentImages || []),
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
    hasVariants: loadedProduct.hasVariants ?? cachedProduct.hasVariants,
    variantBasedOn: loadedProduct.variantBasedOn || cachedProduct.variantBasedOn || '',
    variantOf: loadedProduct.variantOf || cachedProduct.variantOf || '',
    variantLabel: loadedProduct.variantLabel || cachedProduct.variantLabel || '',
    variantAttributes: loadedProduct.variantAttributes?.length
      ? loadedProduct.variantAttributes
      : (cachedProduct.variantAttributes || []),
  }
}

const productImages = computed(() => {
  if (!product.value) {
    return []
  }

  const images = product.value.attachmentImages?.length
    ? product.value.attachmentImages
    : []

  return images.filter(Boolean)
})
const activeProductImage = computed(() =>
  productImages.value[activeImageIndex.value]
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

function getVariantAttributeMap(variant) {
  return Object.fromEntries(
    (variant?.variantAttributes || [])
      .map((attributeRow) => [
        String(attributeRow.attribute || '').trim(),
        String(attributeRow.value || '').trim(),
      ])
      .filter(([attributeName, attributeValue]) => attributeName && attributeValue),
  )
}

function syncSelectedVariantAttributes(variant) {
  selectedVariantAttributes.value = getVariantAttributeMap(variant)
}

function findVariantBySelections(nextSelections) {
  if (!productVariants.value.length) {
    return null
  }

  const exactMatch = productVariants.value.find((variant) => {
    const attributeMap = getVariantAttributeMap(variant)

    return variantAttributeGroups.value.every((group) => (
      attributeMap[group.name] === nextSelections[group.name]
    ))
  })

  if (exactMatch) {
    return exactMatch
  }

  return productVariants.value.find((variant) => {
    const attributeMap = getVariantAttributeMap(variant)

    return Object.entries(nextSelections).every(([attributeName, attributeValue]) => (
      !attributeValue || attributeMap[attributeName] === attributeValue
    ))
  }) || null
}

function getVariantOptionsForAttribute(attributeName) {
  const otherSelections = Object.fromEntries(
    Object.entries(selectedVariantAttributes.value).filter(([name]) => name !== attributeName),
  )

  const matchingVariants = productVariants.value.filter((variant) => {
    const attributeMap = getVariantAttributeMap(variant)

    return Object.entries(otherSelections).every(([name, value]) => (
      !value || attributeMap[name] === value
    ))
  })

  const fallbackVariants = matchingVariants.length ? matchingVariants : productVariants.value
  const options = []

  fallbackVariants.forEach((variant) => {
    const attributeValue = getVariantAttributeMap(variant)[attributeName]

    if (attributeValue && !options.includes(attributeValue)) {
      options.push(attributeValue)
    }
  })

  return options
}

async function loadVariantsForProduct(loadedProduct) {
  const templateItemName = loadedProduct?.variantOf || (loadedProduct?.hasVariants ? loadedProduct.id : '')

  if (!templateItemName) {
    productVariants.value = []
    return false
  }

  isLoadingVariants.value = true

  try {
    const variants = await getProductVariants(templateItemName)
    productVariants.value = variants

    if (loadedProduct?.hasVariants && !loadedProduct?.variantOf && variants.length) {
      const defaultVariant = variants.find((variant) => variant.inStock) || variants[0]

      if (defaultVariant?.id && defaultVariant.id !== route.params.productId) {
        saveSelectedProduct(defaultVariant)
        await router.replace({
          name: 'product-details',
          params: { productId: defaultVariant.id },
        })
        return true
      }
    }

    return false
  } catch {
    productVariants.value = []
    return false
  } finally {
    isLoadingVariants.value = false
  }
}

async function loadProduct() {
  if (!productId.value) {
    loadError.value = 'Product not found.'
    return
  }

  hasProductDetailLoaded.value = false
  const cachedProduct = getSelectedProduct(productId.value)
  product.value = cachedProduct
  productVariants.value = []
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
    const redirectedToVariant = await loadVariantsForProduct(product.value)
    if (redirectedToVariant) {
      return
    }

    syncSelectedVariantAttributes(product.value)
    saveSelectedProduct(product.value)
    activeImageIndex.value = 0
    isProductDescriptionExpanded.value = false
    hasProductDetailLoaded.value = true
  } catch (error) {
    if (!cachedProduct) {
      product.value = null
      productVariants.value = []
      loadError.value = error.message || 'Unable to load product details.'
    }
  } finally {
    isLoading.value = false
  }
}

async function refreshSupplierDistance() {
  if (!product.value) {
    supplierDistanceKm.value = null
    isCheckingDeliverability.value = false
    return
  }

  isCheckingDeliverability.value = true

  try {
    supplierDistanceKm.value = await getCustomerToSupplierDistanceKm(product.value)
  } catch {
    supplierDistanceKm.value = null
  } finally {
    isCheckingDeliverability.value = false
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
  if (product.value && !isOutOfDeliveryRange.value) {
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

async function selectProductVariant(variant) {
  if (!variant?.id || variant.id === productId.value) {
    return
  }

  syncSelectedVariantAttributes(variant)
  saveSelectedProduct(variant)
  await router.push({
    name: 'product-details',
    params: { productId: variant.id },
  })
}

async function updateVariantSelection(attributeName, attributeValue) {
  const nextSelections = {
    ...selectedVariantAttributes.value,
    [attributeName]: attributeValue,
  }

  const matchedVariant = findVariantBySelections(nextSelections)
  if (!matchedVariant) {
    selectedVariantAttributes.value = nextSelections
    return
  }

  await selectProductVariant(matchedVariant)
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

watch(
  () => product.value?.id || '',
  () => {
    refreshSupplierDistance()
  },
  { immediate: true },
)

watch(productSizeOptions, (sizes) => {
  if (!sizes.length) {
    selectedProductSize.value = ''
    return
  }

  if (!sizes.includes(selectedProductSize.value)) {
    selectedProductSize.value = sizes[0]
  }
}, { immediate: true })

onMounted(() => {
  window.addEventListener(LOCATION_UPDATED_EVENT, refreshSupplierDistance)
})

onUnmounted(() => {
  window.removeEventListener(LOCATION_UPDATED_EVENT, refreshSupplierDistance)
})
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

        <section
          v-if="showVariantDropdowns"
          class="product-detail-section product-variant-dropdown-section"
        >
          <h3>Available Options</h3>
          <div class="product-variant-dropdown-grid">
            <label
              v-for="group in variantAttributeGroups"
              :key="group.name"
              class="product-variant-dropdown-field"
            >
              <span>{{ group.name }}</span>
              <select
                :value="selectedVariantAttributes[group.name] || ''"
                @change="updateVariantSelection(group.name, $event.target.value)"
              >
                <option value="" disabled>Select {{ group.name }}</option>
                <option
                  v-for="option in getVariantOptionsForAttribute(group.name)"
                  :key="`${group.name}-${option}`"
                  :value="option"
                >
                  {{ option }}
                </option>
              </select>
            </label>
          </div>
          <p v-if="isLoadingVariants" class="product-variant-status">Loading options...</p>
        </section>

        <section
          v-if="productSizeOptions.length && !showVariantDropdowns"
          class="product-detail-section product-size-section"
        >
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
          <p
            v-if="deliveryStatusMessage"
            class="product-detail-delivery-status"
            :class="{ 'is-blocked': isOutOfDeliveryRange }"
          >
            {{ deliveryStatusMessage }}
          </p>

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
              :disabled="isOutOfDeliveryRange"
              @click="addSelectedProductToCart"
            >
              +
            </button>
          </div>
          <button
            v-else
            class="product-detail-add-button"
            type="button"
            :disabled="isOutOfDeliveryRange"
            @click="addSelectedProductToCart"
          >
            {{ isOutOfDeliveryRange ? 'Not deliverable' : 'Add to cart' }}
          </button>
        </div>
      </aside>
    </article>
  </template>
</template>
