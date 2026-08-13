<script setup>
import { reactive, ref } from 'vue'
import { createSupplier } from '../../api/supplierApi'

const emit = defineEmits(['close', 'created'])

const supplierForm = reactive({
  supplierName: '',
  supplierGroup: 'All Supplier Groups',
  supplierType: 'Company',
  website: '',
  supplierDetails: '',
})
const isSubmitting = ref(false)
const supplierError = ref('')
const supplierMessage = ref('')

function resetForm() {
  supplierForm.supplierName = ''
  supplierForm.supplierGroup = 'All Supplier Groups'
  supplierForm.supplierType = 'Company'
  supplierForm.website = ''
  supplierForm.supplierDetails = ''
}

async function submitSupplier() {
  supplierError.value = ''
  supplierMessage.value = ''
  isSubmitting.value = true

  try {
    const response = await createSupplier(supplierForm)
    const supplier = response.data
    supplierMessage.value = `${supplier.supplier_name || supplier.name} added.`
    emit('created', supplier)
    resetForm()
  } catch (error) {
    supplierError.value = error.message || 'Unable to add supplier.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="supplier-modal-backdrop" role="presentation" @click="$emit('close')">
    <section
      class="supplier-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="supplier-modal-title"
      @click.stop
    >
      <div class="supplier-modal-header">
        <div>
          <p class="section-label">Supplier</p>
          <h2 id="supplier-modal-title">Add supplier</h2>
        </div>
        <button
          class="supplier-modal-close"
          type="button"
          aria-label="Close supplier form"
          @click="$emit('close')"
        >
          ×
        </button>
      </div>

      <form class="supplier-form" @submit.prevent="submitSupplier">
        <label class="field-label" for="supplier-name">Supplier name</label>
        <input
          id="supplier-name"
          v-model="supplierForm.supplierName"
          class="form-input"
          type="text"
          autocomplete="organization"
          required
        />

        <div class="supplier-form-grid">
          <label class="field-label" for="supplier-group">
            Supplier group
            <input
              id="supplier-group"
              v-model="supplierForm.supplierGroup"
              class="form-input"
              type="text"
              required
            />
          </label>

          <label class="field-label" for="supplier-type">
            Supplier type
            <select
              id="supplier-type"
              v-model="supplierForm.supplierType"
              class="form-input"
              required
            >
              <option value="Company">Company</option>
              <option value="Individual">Individual</option>
              <option value="Partnership">Partnership</option>
            </select>
          </label>
        </div>

        <label class="field-label" for="supplier-website">Website</label>
        <input
          id="supplier-website"
          v-model="supplierForm.website"
          class="form-input"
          type="url"
          autocomplete="url"
        />

        <label class="field-label" for="supplier-details">Supplier details</label>
        <textarea
          id="supplier-details"
          v-model="supplierForm.supplierDetails"
          class="form-input supplier-textarea"
          rows="3"
        ></textarea>

        <p v-if="supplierMessage" class="form-message success-message">
          {{ supplierMessage }}
        </p>
        <p v-if="supplierError" class="form-message error-message">
          {{ supplierError }}
        </p>

        <button class="login-button" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Adding supplier...' : 'Add supplier' }}
        </button>
      </form>
    </section>
  </div>
</template>
