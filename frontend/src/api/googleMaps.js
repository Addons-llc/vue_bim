import { GOOGLE_MAPS_API_KEY } from './config'

let googleMapsPromise

export function loadGoogleMaps() {
  if (window.google?.maps) {
    return Promise.resolve(window.google.maps)
  }

  if (!GOOGLE_MAPS_API_KEY) {
    return Promise.reject(new Error('Google Maps API key is missing.'))
  }

  if (!googleMapsPromise) {
    googleMapsPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      const params = new URLSearchParams({
        key: GOOGLE_MAPS_API_KEY,
        libraries: 'places',
        v: 'weekly',
      })

      script.src = `https://maps.googleapis.com/maps/api/js?${params.toString()}`
      script.async = true
      script.defer = true
      script.onload = () => resolve(window.google.maps)
      script.onerror = () => reject(new Error('Unable to load Google Maps.'))

      document.head.appendChild(script)
    })
  }
  return googleMapsPromise
}
