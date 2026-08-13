<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProductById, getProducts } from '../api/productApi'
import { getSupplierDetails } from '../api/supplierApi'
import { getSupplierStore } from '../api/supplierStoreApi'
import ProductCard from '../components/product/ProductCard.vue'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { getSelectedSupplier } from '../data/supplierSelectionStore'

const route = useRoute()
const router = useRouter()
const supplierName = computed(() => String(route.params.supplierName || 'Supplier'))
const selectedSupplier = computed(() => getSelectedSupplier(supplierName.value))
const supplierRecord = ref(null)
const supplierStore = ref(null)
const supplierDetails = computed(() => {
  const store = supplierStore.value
  const supplier = supplierRecord.value || {}
  const selectedDetails = selectedSupplier.value?.details || {}

  return {
    ...selectedDetails,
    ...supplier,
    displayName: store?.name || supplier.displayName || selectedDetails.displayName || supplierName.value,
    storeName: store?.name || selectedDetails.storeName || '',
    supplier: supplier.supplier || store?.supplier || selectedDetails.supplier || '',
    image: store?.image || supplier.image || selectedDetails.image,
    bannerImage: store?.bannerImage || supplier.bannerImage || selectedDetails.bannerImage,
    phone: store?.contactNumber || supplier.phone || selectedDetails.phone,
    email: store?.email || supplier.email || selectedDetails.email,
    website: store?.website || supplier.website || selectedDetails.website,
    details: store?.description || store?.supplierDetails || supplier.details || selectedDetails.details,
    sellerSince: store?.sellerSince || supplier.sellerSince || selectedDetails.sellerSince,
    primaryColour: store?.primaryColour || selectedDetails.primaryColour,
    secondaryColour: store?.secondaryColour || selectedDetails.secondaryColour,
  }
})
const loadedProducts = ref([])
const isLoadingSupplierProducts = ref(false)
const supplierDisplayName = computed(() => supplierDetails.value.displayName || supplierName.value)
const supplierBannerImage = computed(() => supplierDetails.value.bannerImage || supplierDetails.value.image || '')
const supplierProductIds = computed(() => new Set(supplierStore.value?.productIds || []))
const supplierMatchNames = computed(() =>
  new Set([
    supplierName.value,
    supplierRecord.value?.name,
    supplierRecord.value?.supplier,
    supplierRecord.value?.displayName,
    supplierStore.value?.supplier,
    supplierStore.value?.name,
    supplierDetails.value.displayName,
  ].filter(Boolean)),
)
const supplierProducts = computed(() => {
  const products = [
    ...(selectedSupplier.value?.products || []),
    ...loadedProducts.value,
  ]
  const sourceProduct = selectedSupplier.value?.product
  const productIds = supplierProductIds.value
  const matchNames = supplierMatchNames.value

  const relatedProducts = products.filter((product) => {
    if (productIds.size) {
      return [
        product.id,
        product.itemCode,
        product.name,
      ].some((value) => productIds.has(value))
    }

    return matchNames.has(product.supplierName || product.supplier || 'Supplier not set')
  })
  const productMap = relatedProducts.reduce((productsById, product) => {
    if (product?.id) {
      productsById.set(product.id, product)
    }

    return productsById
  }, new Map())

  const shouldIncludeSourceProduct = sourceProduct?.id && (
    !productIds.size
    || [sourceProduct.id, sourceProduct.itemCode, sourceProduct.name].some((value) => productIds.has(value))
  )

  if (shouldIncludeSourceProduct && !productMap.has(sourceProduct.id)) {
    productMap.set(sourceProduct.id, sourceProduct)
  }

  return Array.from(productMap.values()).filter((product) => product.isPublished !== false)
})
const supplierInitials = computed(() => supplierDisplayName.value.slice(0, 2).toUpperCase())
const storeName = computed(() => supplierDetails.value.storeName || '')
const storeSupplierName = computed(() => supplierDetails.value.supplier || '')
const supplierPhone = computed(() => supplierDetails.value.phone || '')
const supplierEmail = computed(() => supplierDetails.value.email || '')
const supplierWebsite = computed(() => supplierDetails.value.website || '')
const supplierDescription = computed(() => supplierDetails.value.details || '')
const supplierSince = computed(() => supplierDetails.value.sellerSince || '')
const hasSupplierContact = computed(() =>
  Boolean(supplierPhone.value || supplierEmail.value || supplierWebsite.value),
)
const hasSupplierInfo = computed(() =>
  Boolean(storeName.value || storeSupplierName.value || supplierDescription.value || supplierWebsite.value),
)

function openProductDetails(product) {
  saveSelectedProduct(product)

  router.push({
    name: 'product-details',
    params: { productId: product.id },
  })
}

function showSupplierBannerFallback(event) {
  if (!supplierDetails.value.image || event.target.src === supplierDetails.value.image) {
    return
  }

  event.target.src = supplierDetails.value.image
}

async function loadSupplierProducts() {
  isLoadingSupplierProducts.value = true

  try {
    const [loadedStore, details] = await Promise.all([
      getSupplierStore(supplierName.value).catch(() => null),
      getSupplierDetails(supplierName.value).catch(() => null),
    ])

    supplierStore.value = loadedStore
    supplierRecord.value = details

    const store = supplierStore.value
    const supplierFilter = supplierRecord.value?.supplier || store?.supplier || supplierName.value
    const products = await getProducts({
      limit_page_length: 5000,
      supplier: supplierFilter,
      supplier_store: store?.storeCode || store?.id,
    })

    if (store?.productIds?.length) {
      const missingProductIds = store.productIds.filter((productId) =>
        !products.some((product) =>
          [product.id, product.itemCode, product.name].includes(productId),
        ),
      )
      const associatedProducts = await Promise.all(
        missingProductIds.map((productId) => getProductById(productId).catch(() => null)),
      )

      loadedProducts.value = [
        ...products,
        ...associatedProducts.filter(Boolean),
      ]
      return
    }

    loadedProducts.value = products
  } catch {
    supplierRecord.value = null
    loadedProducts.value = []
  } finally {
    isLoadingSupplierProducts.value = false
  }
}

onMounted(loadSupplierProducts)

watch(supplierName, () => {
  supplierRecord.value = null
  supplierStore.value = null
  loadedProducts.value = []
  loadSupplierProducts()
})
</script>

<template>
  <section
    class="supplier-detail-page"
  >
    <aside class="supplier-profile-panel">
      <div class="supplier-profile-header">
        <span class="supplier-profile-logo">
          <img
            v-if="supplierDetails.image"
            :src="supplierDetails.image"
            :alt="`${supplierDisplayName} logo`"
          />
          <span v-else>{{ supplierInitials }}</span>
        </span>
        <h1>{{ supplierDisplayName }}</h1>
      </div>
      <p v-if="supplierDescription" class="supplier-profile-summary">{{ supplierDescription }}</p>
      <div v-if="hasSupplierContact" class="supplier-profile-contact">
        <span v-if="supplierPhone">☏ {{ supplierPhone }}</span>
        <span v-if="supplierEmail">✉ {{ supplierEmail }}</span>
        <a
          v-if="supplierWebsite"
          :href="supplierWebsite"
          target="_blank"
          rel="noreferrer"
        >
          ⌁ {{ supplierWebsite }}
        </a>
      </div>

      <section v-if="hasSupplierInfo" class="supplier-profile-info" aria-label="Supplier information">
        <div v-if="storeName" class="supplier-profile-info-row">
          <span>Store Name</span>
          <p>{{ storeName }}</p>
        </div>
        <div v-if="storeSupplierName" class="supplier-profile-info-row">
          <span>Supplier</span>
          <p>{{ storeSupplierName }}</p>
        </div>
        <div v-if="supplierDescription" class="supplier-profile-info-row">
          <span>Supplier Details</span>
          <p>{{ supplierDescription }}</p>
        </div>
      </section>

      <div v-if="supplierSince" class="supplier-profile-since">
        <span>Seller Since</span>
        <strong>{{ supplierSince }}</strong>
      </div>
    </aside>

    <main class="supplier-store-main">
      <div class="supplier-store-banner">
        <img
          v-if="supplierBannerImage"
          class="supplier-store-banner-image"
          :src="supplierBannerImage"
          :alt="`${supplierDisplayName} banner`"
          @error="showSupplierBannerFallback"
        />
        <span class="supplier-banner-logo">
          <img
            v-if="supplierDetails.image"
            :src="supplierDetails.image"
            :alt="`${supplierDisplayName} logo`"
          />
          <span v-else>{{ supplierInitials }}</span>
        </span>
        <strong>{{ supplierDescription || supplierDisplayName }}</strong>
      </div>

      <section class="supplier-products-panel">
        <h2>Products by {{ supplierDisplayName }}</h2>
        <p v-if="isLoadingSupplierProducts" class="dashboard-message">
          Loading more products...
        </p>
        <div v-if="supplierProducts.length" class="supplier-products-grid">
          <ProductCard
            v-for="product in supplierProducts"
            :key="product.id"
            :product="product"
            compact
            @select="openProductDetails"
          />
        </div>
        <p v-else class="dashboard-message">No published products found for this supplier.</p>
      </section>
    </main>
  </section>
</template>
