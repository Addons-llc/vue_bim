import { computed, ref } from 'vue'

const CART_STORAGE_KEY = 'buyInMinutesCart'

function isTruthyFlag(value) {
  return value === true || value === 1 || value === '1' || value === 'Yes'
}

function toNumber(value) {
  const numberValue = Number(value)

  return Number.isFinite(numberValue) ? numberValue : 0
}

function readStoredCart() {
  try {
    const storedItems = JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) || []

    return Array.isArray(storedItems)
      ? storedItems.map((item) => ({
        ...item,
        customDeliverySlots: isTruthyFlag(
          item?.customDeliverySlots ?? item?.custom_delivery_slots,
        ),
        customDeliveryFee: toNumber(
          item?.customDeliveryFee ?? item?.custom_delivery_fee,
        ),
      }))
      : []
  } catch {
    return []
  }
}

function saveCart(items) {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items))
}

const cartItems = ref(readStoredCart())

export const cartProducts = cartItems

export const cartItemCount = computed(() => cartItems.value.length)

export const cartTotal = computed(() =>
  cartItems.value.reduce((total, item) => total + item.price * item.quantity, 0),
)

export function addProductToCart(product) {
  const selectedSize = String(product.selectedSize || product.size || '').trim()
  const existingItem = cartItems.value.find((item) => item.id === product.id)
  const productRequiresDeliverySlot = isTruthyFlag(
    product.customDeliverySlots ?? product.custom_delivery_slots,
  )
  let cartItem

  if (existingItem) {
    existingItem.quantity += 1
    if (selectedSize) {
      existingItem.size = selectedSize
    }
    existingItem.customDeliverySlots = isTruthyFlag(
      existingItem.customDeliverySlots ?? existingItem.custom_delivery_slots,
    ) || productRequiresDeliverySlot
    existingItem.customDeliveryFee = toNumber(
      existingItem.customDeliveryFee ?? product.customDeliveryFee ?? product.custom_delivery_fee,
    )
    cartItem = existingItem
  } else {
    cartItem = {
      id: product.id,
      itemCode: product.itemCode || product.id,
      name: product.name,
      price: product.price,
      oldPrice: product.oldPrice,
      description: product.description,
      image: product.image,
      supplier: product.supplier || product.supplierDetails?.name || '',
      supplierName: product.supplierName,
      supplierDetails: product.supplierDetails || null,
      supplierAddress: product.supplierAddress || product.supplierDetails?.customGoogleAddress || '',
      supplierLatitude: product.supplierLatitude || product.supplierDetails?.customLatitude || '',
      supplierLongitude: product.supplierLongitude || product.supplierDetails?.customLongitude || '',
      customDeliveryFee: toNumber(product.customDeliveryFee ?? product.custom_delivery_fee),
      size: selectedSize,
      customDeliverySlots: productRequiresDeliverySlot,
      quantity: 1,
    }
    cartItems.value.push(cartItem)
  }

  saveCart(cartItems.value)

  return {
    success: true,
    item: { ...cartItem },
    cart_item_count: cartItemCount.value,
    cart_total: cartTotal.value,
  }
}

export function getCartItems() {
  return cartItems.value
}

export function updateCartProductQuantity(productId, quantity) {
  if (quantity <= 0) {
    removeProductFromCart(productId)
    return
  }

  const existingItem = cartItems.value.find((item) => item.id === productId)

  if (!existingItem) {
    return
  }

  existingItem.quantity = quantity
  saveCart(cartItems.value)
}

export function removeProductFromCart(productId) {
  cartItems.value = cartItems.value.filter((item) => item.id !== productId)
  saveCart(cartItems.value)
}

export function clearCart() {
  cartItems.value = []
  saveCart(cartItems.value)
}
