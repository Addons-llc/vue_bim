import { ref } from 'vue'

const ADDRESS_STORAGE_KEY = 'buyInMinutesCustomerAddresses'

function createAddressId() {
  return `address-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function readStoredAddresses() {
  try {
    const addresses = JSON.parse(localStorage.getItem(ADDRESS_STORAGE_KEY))

    return Array.isArray(addresses) ? addresses : []
  } catch {
    return []
  }
}

function persistAddresses() {
  localStorage.setItem(ADDRESS_STORAGE_KEY, JSON.stringify(customerAddresses.value))
}

export const customerAddresses = ref(readStoredAddresses())

export function addCustomerAddress(address) {
  const shouldSetDefault = !customerAddresses.value.length || address.isDefault
  const nextAddress = {
    id: createAddressId(),
    label: address.label.trim(),
    contactName: address.contactName.trim(),
    phone: address.phone.trim(),
    email: (address.email || '').trim(),
    area: address.area.trim(),
    apartmentOfficeName: (address.apartmentOfficeName || '').trim(),
    apartmentOfficeNo: (address.apartmentOfficeNo || '').trim(),
    building: address.building.trim(),
    street: address.street.trim(),
    landmark: address.landmark.trim(),
    emirate: address.emirate.trim(),
    latitude: address.latitude || '',
    longitude: address.longitude || '',
    isDefault: shouldSetDefault,
  }

  customerAddresses.value = [
    ...(shouldSetDefault ? customerAddresses.value.map((item) => ({ ...item, isDefault: false })) : customerAddresses.value),
    nextAddress,
  ]
  persistAddresses()
}

export function updateCustomerAddress(addressId, address) {
  const shouldSetDefault = address.isDefault

  customerAddresses.value = customerAddresses.value.map((item) => {
    if (item.id !== addressId) {
      return shouldSetDefault ? { ...item, isDefault: false } : item
    }

    return {
      ...item,
      label: address.label.trim(),
      contactName: address.contactName.trim(),
      phone: address.phone.trim(),
      email: (address.email || '').trim(),
      area: address.area.trim(),
      apartmentOfficeName: (address.apartmentOfficeName || '').trim(),
      apartmentOfficeNo: (address.apartmentOfficeNo || '').trim(),
      building: address.building.trim(),
      street: address.street.trim(),
      landmark: address.landmark.trim(),
      emirate: address.emirate.trim(),
      latitude: address.latitude || '',
      longitude: address.longitude || '',
      isDefault: shouldSetDefault || item.isDefault,
    }
  })
  persistAddresses()
}

export function removeCustomerAddress(addressId) {
  const removedAddress = customerAddresses.value.find((address) => address.id === addressId)
  const remainingAddresses = customerAddresses.value.filter((address) => address.id !== addressId)

  if (removedAddress?.isDefault && remainingAddresses.length) {
    remainingAddresses[0] = {
      ...remainingAddresses[0],
      isDefault: true,
    }
  }

  customerAddresses.value = remainingAddresses
  persistAddresses()
}

export function setDefaultCustomerAddress(addressId) {
  customerAddresses.value = customerAddresses.value.map((address) => ({
    ...address,
    isDefault: address.id === addressId,
  }))
  persistAddresses()
}
